# -*- coding: utf-8 -*-
"""SharedMemoryIPC Low-Level Driver.

이 모듈은 공유 메모리(Shared Memory)와 파일 락(File Lock)을 이용하여
Windows, Linux, macOS 등 다중 OS 환경에서 작동하는 독립 에이전트 간 고속 IPC 통신을 지원합니다.
"""

import json
import logging
import os
import struct
import sys
import time
from multiprocessing import shared_memory
from typing import Any, Dict, Optional, Tuple

# 로깅 설정
logger = logging.getLogger("SharedMemoryIPC.Driver")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 상수 정의
DEFAULT_SHM_SIZE = 1048576  # 1MB
HEADER_SIZE = 64  # Bytes
SLOT_SIZE = 4096  # Bytes
MAX_SLOTS = (DEFAULT_SHM_SIZE - HEADER_SIZE) // SLOT_SIZE  # 255 Slots

# Magic 바이트 정의
HEADER_MAGIC = b"SIPC"
SLOT_MAGIC = b"MSLT"

# 포맷 정의 (struct 모듈 규격)
# Header: magic(4s), version(H), shm_size(Q), write_index(Q), read_index(Q), lock_state(L), msg_count(L), reserved(26s)
HEADER_FORMAT = "<4s H Q Q Q L L 26s"
# Slot: magic(4s), msg_id(Q), timestamp(Q), sender_id(32s), command(64s), payload_len(L), payload(3976s)
SLOT_FORMAT = "<4s Q Q 32s 64s L 3976s"


class SharedMemoryIPCError(Exception):
    """SharedMemoryIPC 최상위 예외 클래스."""

    pass


class SharedMemoryIPCLockError(SharedMemoryIPCError):
    """동시성 제어용 파일 락 획득 실패 시 발생합니다."""

    pass


class SharedMemoryIPCBufferOverflow(SharedMemoryIPCError):
    """버퍼 슬롯이 가득 찼거나 페이로드 한도를 초과했을 때 발생합니다."""

    pass


class CrossPlatformFileLock:
    """Windows, Linux, macOS를 모두 지원하는 OS 수준의 파일 시스템 락(Mutex) 구현체."""

    def __init__(self, lock_file_path: str):
        """임시 디렉토리 아래의 락 파일 경로를 설정합니다.

        Args:
            lock_file_path: 락 파일의 절대 경로
        """
        self.lock_file_path = lock_file_path
        self.file_handle = None

    def acquire(self, timeout: float = 2.0) -> bool:
        """배타적(Exclusive) 파일 락을 획득합니다.

        Args:
            timeout: 락 획득을 대기할 최대 시간(초)

        Returns:
            bool: 락 획득 성공 여부

        Raises:
            SharedMemoryIPCLockError: 타임아웃 내에 락을 획득하지 못했을 경우
        """
        start_time = time.time()
        while True:
            try:
                # 락 파일 생성 및 열기
                self.file_handle = open(self.lock_file_path, "w")

                if sys.platform == "win32":
                    import msvcrt

                    # Windows 배타적 락 시도 (msvcrt.LK_NBLCK: Non-blocking lock)
                    msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    # POSIX 배타적 락 시도 (fcntl.LOCK_EX | fcntl.LOCK_NB: Non-blocking)
                    fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # 락 획득 성공
                return True
            except (IOError, OSError):
                # 파일 핸들러 정리 후 대기
                if self.file_handle:
                    try:
                        self.file_handle.close()
                    except Exception:
                        pass
                    self.file_handle = None

                if time.time() - start_time > timeout:
                    raise SharedMemoryIPCLockError(
                        f"락 획득 타임아웃 ({timeout}s 초과): '{self.lock_file_path}'"
                    )
                time.sleep(0.05)  # 50ms 대기 후 재시도

    def release(self) -> None:
        """획득한 파일 락을 해제하고 핸들을 닫습니다."""
        if self.file_handle:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    # Windows 락 해제
                    self.file_handle.seek(0)
                    msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    # POSIX 락 해제
                    fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_UN)
            except (IOError, OSError) as e:
                logger.warning(f"락 해제 중 예외 발생: {str(e)}")
            finally:
                try:
                    self.file_handle.close()
                except Exception:
                    pass
                self.file_handle = None


class SharedMemoryIPCDriver:
    """공유 메모리와 크로스 플랫폼 파일 락을 관리하는 로우레벨 에이전트 IPC 드라이버."""

    def __init__(self, shm_name: str, size: int = DEFAULT_SHM_SIZE, create: bool = False):
        """드라이버 인스턴스를 초기화하고 공유 메모리에 바인딩합니다.

        Args:
            shm_name: 공유 메모리 고유 식별 명칭
            size: 할당할 공유 메모리 물리 크기 (기본 1MB)
            create: True인 경우 공유 메모리를 새로 생성, False인 경우 기존 영역에 바인딩
        """
        self.shm_name = shm_name
        self.size = size
        self.create = create
        self.shm = None

        # 임시 디렉토리 하위에 OS 독립적인 락 파일 경로 설정
        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
        self.lock_path = os.path.join(temp_dir, f"{shm_name}.lock")
        self.mutex = CrossPlatformFileLock(self.lock_path)

        # 에이전트 로컬 메시지 포인터 (마지막으로 읽은 메시지 ID)
        self.last_read_id = 0

        self._initialize_shm()

    def _initialize_shm(self) -> None:
        """공유 메모리를 연결하거나 생성하며, 생성 시 메타데이터 헤더를 구성합니다."""
        try:
            if self.create:
                # 기존에 같은 이름의 공유 메모리가 남아있다면 강제 해제 시도
                try:
                    old_shm = shared_memory.SharedMemory(name=self.shm_name)
                    old_shm.close()
                    old_shm.unlink()
                    logger.info(f"기존 공유 메모리 리소스를 안전하게 리셋했습니다: '{self.shm_name}'")
                except FileNotFoundError:
                    pass

                self.shm = shared_memory.SharedMemory(
                    name=self.shm_name, create=True, size=self.size
                )
                logger.info(f"공유 메모리 영역을 새로 생성했습니다: '{self.shm_name}' (Size: {self.size} bytes)")
                self._write_initial_header()
            else:
                self.shm = shared_memory.SharedMemory(name=self.shm_name)
                logger.info(f"기존 공유 메모리 영역에 바인딩되었습니다: '{self.shm_name}'")
                self._verify_header()
        except Exception as e:
            raise SharedMemoryIPCError(f"공유 메모리 바인딩 실패 ('{self.shm_name}'): {str(e)}")

    def _write_initial_header(self) -> None:
        """공유 메모리 생성 직후 SIPC 규격에 따른 초기 헤더 레코드를 기록합니다."""
        # Header 규격: magic, version, size, write_index, read_index, lock_state, msg_count, reserved
        header_data = struct.pack(
            HEADER_FORMAT,
            HEADER_MAGIC,
            1,  # Version: 1
            self.size,
            0,  # write_index: 0
            0,  # read_index: 0
            0,  # lock_state: 0 (Unlocked)
            0,  # msg_count: 0
            b"\x00" * 26,  # Reserved padding
        )
        self.shm.buf[0:HEADER_SIZE] = header_data

    def _verify_header(self) -> None:
        """바인딩된 공유 메모리 헤더가 올바른 SIPC 프로토콜 규격인지 검증합니다."""
        if not self.shm:
            raise SharedMemoryIPCError("공유 메모리 영역이 연결되어 있지 않거나 이미 정리되었습니다.")
        header_bytes = bytes(self.shm.buf[0:HEADER_SIZE])
        magic, version, size, _, _, _, _, _ = struct.unpack(HEADER_FORMAT, header_bytes)
        if magic != HEADER_MAGIC:
            raise SharedMemoryIPCError("유효하지 않은 SIPC 프로토콜 매직 바이트입니다.")
        logger.debug(f"SIPC 검증 통과 - Version: {version}, Size: {size}")

    def _read_header(self) -> Tuple[int, int, int]:
        """공유 메모리 헤더에서 인덱스 및 미처리 메시지 개수를 언팩하여 반환합니다.

        Returns:
            Tuple[int, int, int]: (write_index, read_index, msg_count)
        """
        if not self.shm:
            raise SharedMemoryIPCError("공유 메모리 영역이 연결되어 있지 않거나 이미 정리되었습니다.")
        header_bytes = bytes(self.shm.buf[0:HEADER_SIZE])
        _, _, _, write_index, read_index, _, msg_count, _ = struct.unpack(
            HEADER_FORMAT, header_bytes
        )
        return write_index, read_index, msg_count

    def _write_header_indices(self, write_index: int, read_index: int, msg_count: int) -> None:
        """헤더의 인덱스 정보를 원자적으로 갱신합니다. (반드시 락 획득 후 실행)"""
        if not self.shm:
            raise SharedMemoryIPCError("공유 메모리 영역이 연결되어 있지 않거나 이미 정리되었습니다.")
        # 기존 보존 데이터를 위해 헤더 언팩 후 인덱스만 덮어쓰기
        header_bytes = bytes(self.shm.buf[0:HEADER_SIZE])
        magic, version, size, _, _, lock_state, _, reserved = struct.unpack(
            HEADER_FORMAT, header_bytes
        )

        new_header = struct.pack(
            HEADER_FORMAT,
            magic,
            version,
            size,
            write_index,
            read_index,
            lock_state,
            msg_count,
            reserved,
        )
        self.shm.buf[0:HEADER_SIZE] = new_header

    def write_message(self, sender_id: str, command: str, payload: Dict[str, Any]) -> int:
        """공유 메모리 링 버퍼에 새로운 에이전트 메시지를 기록합니다.

        Args:
            sender_id: 송신 에이전트 고유 식별자 (최대 32자)
            command: 처리할 명령어 문자열 (최대 64자)
            payload: 직렬화하여 본문에 실을 사전(Dict) 데이터 (JSON 인코딩 후 3976 바이트 제한)

        Returns:
            int: 기록에 성공한 전역 고유 메시지 ID (msg_id)

        Raises:
            SharedMemoryIPCBufferOverflow: 페이로드 한도 초과 또는 드라이버 한도 초과 시
            SharedMemoryIPCLockError: 동시성 락 획득 실패 시
        """
        # payload JSON 직렬화 및 검증
        try:
            payload_str = json.dumps(payload, ensure_ascii=False)
            payload_bytes = payload_str.encode("utf-8")
        except Exception as e:
            raise SharedMemoryIPCError(f"Payload JSON 직렬화 실패: {str(e)}")

        if len(payload_bytes) > 3976:
            raise SharedMemoryIPCBufferOverflow(
                f"메시지 본문 크기 한도 초과 ({len(payload_bytes)} > 3976 Bytes)"
            )

        # Null-padding bytes 구성
        sender_bytes = sender_id.encode("utf-8")[:32].ljust(32, b"\x00")
        command_bytes = command.encode("utf-8")[:64].ljust(64, b"\x00")
        payload_bytes_padded = payload_bytes.ljust(3976, b"\x00")

        # 파일 락을 통한 임계 영역 동시성 보장
        self.mutex.acquire()
        try:
            write_index, read_index, msg_count = self._read_header()

            # 신규 메시지 고유 ID 발급 (write_index 자체가 증가하는 시퀀스 역할을 수행)
            msg_id = write_index + 1
            timestamp = int(time.time() * 1000)

            # Slot 이진 패킹
            # Slot: magic, msg_id, timestamp, sender_id, command, payload_len, payload
            slot_data = struct.pack(
                SLOT_FORMAT,
                SLOT_MAGIC,
                msg_id,
                timestamp,
                sender_bytes,
                command_bytes,
                len(payload_bytes),
                payload_bytes_padded,
            )

            # 링 버퍼 상의 슬롯 물리 인덱스 오프셋 계산
            slot_idx = write_index % MAX_SLOTS
            offset = HEADER_SIZE + (slot_idx * SLOT_SIZE)

            # 메모리에 직접 쓰기
            self.shm.buf[offset : offset + SLOT_SIZE] = slot_data

            # 링 버퍼 헤더 갱신 (write_index 1 증가)
            new_write_idx = write_index + 1
            new_msg_count = min(msg_count + 1, MAX_SLOTS)

            # 만약 링 버퍼가 완전히 한 바퀴 돌아서 읽지 않은 데이터를 덮어쓰게 되는 경우
            # read_index를 한 칸 강제 전진하여 버퍼 구조를 보존합니다.
            new_read_idx = read_index
            if new_msg_count == MAX_SLOTS and write_index >= MAX_SLOTS:
                new_read_idx = new_write_idx - MAX_SLOTS

            self._write_header_indices(new_write_idx, new_read_idx, new_msg_count)

            logger.debug(
                f"메시지 쓰기 성공 - ID: {msg_id}, Slot: {slot_idx}, Comm: {command}"
            )
            return msg_id

        finally:
            self.mutex.release()

    def read_next_message(self, reader_id: str) -> Optional[Dict[str, Any]]:
        """에이전트가 마지막으로 읽은 포인터 다음의 신규 메시지를 한 개 폴링하여 반환합니다.

        Args:
            reader_id: 수신 에이전트 식별자

        Returns:
            Optional[Dict[str, Any]]: 새로운 메시지 객체, 신규 메시지가 없을 경우 None 반환
        """
        self.mutex.acquire()
        try:
            write_index, read_index, _ = self._read_header()

            # 만약 에이전트 로컬 포인터가 링 버퍼의 읽기 가능한 하한선(read_index)보다 밀렸을 경우
            # 유실을 방지하고 가능한 가장 오래된 유효 메시지로 포인터를 강제 보정합니다.
            if self.last_read_id < read_index:
                self.last_read_id = read_index
                logger.warning(
                    f"에이전트 '{reader_id}'의 읽기 포인터가 링 버퍼 하한선 뒤로 밀려 강제 보정되었습니다: "
                    f"{self.last_read_id} -> {read_index}"
                )

            # 읽을 신규 메시지가 없는 경우
            if self.last_read_id >= write_index:
                return None

            # 읽을 슬롯 오프셋 계산
            slot_idx = self.last_read_id % MAX_SLOTS
            offset = HEADER_SIZE + (slot_idx * SLOT_SIZE)

            # 슬롯 이진 데이터 복사 후 락 영역 최소화를 위해 언팩 및 파싱은 로컬 스택에서 수행
            slot_bytes = bytes(self.shm.buf[offset : offset + SLOT_SIZE])

            # 읽기 포인터 증가
            self.last_read_id += 1

        finally:
            self.mutex.release()

        # 이진 데이터 언패킹
        # Slot: magic, msg_id, timestamp, sender_id, command, payload_len, payload
        magic, msg_id, timestamp, sender_b, command_b, payload_len, payload_b = struct.unpack(
            SLOT_FORMAT, slot_bytes
        )

        if magic != SLOT_MAGIC:
            logger.error(
                f"유효하지 않은 슬롯 매직 바이트 검출 (Slot: {slot_idx}). 원시 데이터를 건너뜁니다."
            )
            return None

        # 디코딩 및 Null 스트립 처리
        sender_id_str = sender_b.decode("utf-8").rstrip("\x00")
        command_str = command_b.decode("utf-8").rstrip("\x00")
        payload_bytes = payload_b[:payload_len]

        try:
            payload_data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"메시지 페이로드 JSON 디코딩 실패 (ID: {msg_id}): {str(e)}")
            payload_data = {"error": "JSON 디코딩 실패", "raw": payload_bytes.decode("utf-8", errors="ignore")}

        return {
            "msg_id": msg_id,
            "timestamp": timestamp,
            "sender_id": sender_id_str,
            "command": command_str,
            "payload": payload_data,
        }

    def close(self) -> None:
        """공유 메모리 매핑 참조를 닫습니다. (인스턴스 소멸 시 안전장치)"""
        if self.shm:
            try:
                self.shm.close()
                logger.info(f"공유 메모리 매핑을 해제했습니다: '{self.shm_name}'")
            except Exception as e:
                logger.warning(f"공유 메모리 닫기 실패: {str(e)}")
            finally:
                self.shm = None

    def destroy(self) -> None:
        """공유 메모리 인프라 및 파일 락 임시 파일을 물리적으로 파괴 및 완전 삭제합니다."""
        self.close()
        try:
            # 공유 메모리 완전히 OS 메모리풀에서 삭제 (unlink)
            shm_temp = shared_memory.SharedMemory(name=self.shm_name)
            shm_temp.unlink()
            logger.info(f"공유 메모리를 OS 수준에서 해제(Unlink)했습니다: '{self.shm_name}'")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"공유 메모리 Unlink 실패: {str(e)}")

        # 락 임시 파일 삭제
        if os.path.exists(self.lock_path):
            try:
                os.remove(self.lock_path)
                logger.info(f"임시 락 파일 제거 완료: '{self.lock_path}'")
            except Exception as e:
                logger.warning(f"락 파일 제거 실패: {str(e)}")

    def __enter__(self) -> "SharedMemoryIPCDriver":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
