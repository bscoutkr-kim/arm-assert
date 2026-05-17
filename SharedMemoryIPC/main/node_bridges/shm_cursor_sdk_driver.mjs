#!/usr/bin/env node
/**
 * SharedMemoryIPC Rule-Aware Cursor SDK Subprocess Bridge.
 * 
 * 1. JSON 입력(stdin): prompt, model, cwd(에이전트 작업 공간), targetFile(수정 대상 파일)
 * 2. Rule Collector가 지정된 cwd의 AGENTS.md, GEMINI.md 및 관련 스킬 reference.md를 수집
 * 3. 조립된 시스템 프롬프트와 함께 @cursor/sdk 에이전트 구동
 * 4. 결과 출력: stdout에 { success, text } 한 줄(JSON)
 */

import { readFileSync, existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { homedir } from "node:os";
import { execSync } from "node:child_process";
import { Agent } from "@cursor/sdk";

// --- 환경 변수 및 설정 해결 ---

function resolveConfigRoot() {
    return process.env.MYSTOCK_CONFIG_ROOT?.trim() || path.join(homedir(), "auto-trading-test-config");
}

function resolveApiKey() {
    if (process.env.CURSOR_API_KEY) return process.env.CURSOR_API_KEY;
    const keysPath = path.join(resolveConfigRoot(), "APIKEY", "llm_api_keys.json");
    if (!existsSync(keysPath)) throw new Error(`API key file not found: ${keysPath}`);
    const keys = JSON.parse(readFileSync(keysPath, "utf8").replace(/^\uFEFF/, ""));
    return keys.cursor?.apiKey;
}

function setupRipgrep() {
    if (process.env.CURSOR_RIPGREP_PATH) return;
    try {
        const cmd = process.platform === "win32" ? "where rg" : "command -v rg";
        const rgPath = execSync(cmd, { encoding: "utf8" }).split(/\r?\n/)[0]?.trim();
        if (rgPath && path.isAbsolute(rgPath)) {
            process.env.CURSOR_RIPGREP_PATH = rgPath;
        }
    } catch (e) {
        // Ripgrep 누락 시 경고
    }
}

// --- Rule Collector & Assembler ---

function assembleSystemPrompt(workspaceRoot, targetFile) {
    const rules = [];

    // 1. 공통 코딩 룰셋 로드 (AGENTS.md)
    const agentsPath = path.join(workspaceRoot, "AGENTS.md");
    if (existsSync(agentsPath)) {
        rules.push(`### [공통 코딩 룰셋 - AGENTS.md] ###\n${readFileSync(agentsPath, "utf8")}`);
    }

    // 2. 공통 관리 감사 룰셋 로드 (GEMINI.md)
    const geminiPath = path.join(workspaceRoot, "GEMINI.md");
    if (existsSync(geminiPath)) {
        rules.push(`### [공통 관리 감사 룰셋 - GEMINI.md] ###\n${readFileSync(geminiPath, "utf8")}`);
    }

    // 3. 파일명 및 도메인 분석 기반 특정 검증 스킬셋 reference.md 동적 매핑
    const skillsDir = path.join(workspaceRoot, ".agent", "skills");
    if (existsSync(skillsDir) && targetFile) {
        try {
            const skillFolders = readdirSync(skillsDir);
            const targetLower = targetFile.toLowerCase();

            for (const folder of skillFolders) {
                // 특정 키워드(grid, order, settings 등)를 포함하는 폴더가 검출되면 해당 스킬 reference.md 병합
                const skillKeyword = folder.replace("verify-", "");
                if (targetLower.includes(skillKeyword)) {
                    const refPath = path.join(skillsDir, folder, "reference.md");
                    if (existsSync(refPath)) {
                        rules.push(`### [도메인 특정 검증 스킬 - ${folder}/reference.md] ###\n${readFileSync(refPath, "utf8")}`);
                    }
                }
            }
        } catch (err) {
            // 스킬 디렉토리 파싱 실패 시 조용히 스킵
        }
    }

    if (rules.length === 0) {
        return "너는 범용 소프트웨어 코딩 도우미이다. 무결하고 정밀한 최선의 코드를 생성하라.";
    }

    return `너는 지정된 프로젝트의 규칙과 규격을 철두철미하게 엄수하여 코드를 작성하는 전문 에이전트이다.
아래의 모든 코딩 룰과 검증 표준을 단 1%도 타협하거나 위배하지 말고, 외과수술적으로 정밀하게 타겟 파일의 수정을 수행하라.

${rules.join("\n\n")}`;
}

/** Collect deliverable assistant text only (exclude thinking stream). */
function appendSdkMessageText(event, parts) {
    if (!event || typeof event !== "object") return;
    if (event.type === "assistant" && Array.isArray(event.message?.content)) {
        for (const block of event.message.content) {
            if (block?.type === "text" && block.text) {
                parts.push(block.text);
            }
        }
    }
}

// --- 메인 실행 로직 ---

async function main() {
    let inputData;
    try {
        const arg = process.argv[2];
        if (arg) {
            inputData = JSON.parse(arg);
        } else {
            const stdin = readFileSync(0, "utf8");
            inputData = JSON.parse(stdin);
        }
    } catch (e) {
        console.error(JSON.stringify({ success: false, error: "Invalid JSON input" }));
        process.exit(1);
    }

    const { prompt, model = "composer-2", cwd: workspaceRoot, targetFile } = inputData;
    if (!prompt) {
        console.error(JSON.stringify({ success: false, error: "Prompt is required" }));
        process.exit(1);
    }

    let agent = null;
    try {
        const apiKey = resolveApiKey();
        if (!apiKey) throw new Error("Cursor API key not found in config");

        setupRipgrep();

        const agentCwd =
            typeof workspaceRoot === "string" &&
            workspaceRoot.trim() !== "" &&
            path.isAbsolute(workspaceRoot.trim())
                ? workspaceRoot.trim()
                : process.cwd();

        // 룰셋 동적 조립
        const systemPrompt = assembleSystemPrompt(agentCwd, targetFile);

        agent = await Agent.create({
            apiKey,
            model: { id: model },
            local: { cwd: agentCwd },
        });

        // 룰을 시스템 프롬프트 가드로 얹어서 송신
        const run = await agent.send(prompt, {
            systemPrompt: systemPrompt
        });

        const parts = [];
        for await (const event of run.stream()) {
            appendSdkMessageText(event, parts);
        }

        const waitResult = await run.wait();
        let fullText = parts.join("").trim();
        if (!fullText && typeof run.result === "string") {
            fullText = run.result.trim();
        }
        if (!fullText && waitResult?.result) {
            fullText = String(waitResult.result).trim();
        }

        if (!fullText) {
            console.log(
                JSON.stringify({
                    success: false,
                    error: "Agent returned no text content",
                    status: run.status,
                    agentId: agent.agentId,
                })
            );
            process.exit(1);
        }

        console.log(
            JSON.stringify({
                success: true,
                text: fullText,
                status: run.status,
                agentId: agent.agentId,
            })
        );

    } catch (err) {
        console.log(JSON.stringify({
            success: false,
            error: err.message
        }));
        process.exit(1);
    } finally {
        if (agent) agent.close();
    }
}

main();
