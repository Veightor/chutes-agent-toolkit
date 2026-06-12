// Chutes chat + streaming with the OpenAI SDK. [VERIFIED 2026-06-11: ran live against the paid API]
// Setup: npm install openai
// Run:   CHUTES_API_KEY="<redacted>" node chat.mjs

import OpenAI from "openai";

const MODEL = process.env.CHUTES_MODEL ?? "unsloth/Mistral-Nemo-Instruct-2407-TEE";

const client = new OpenAI({
  baseURL: "https://llm.chutes.ai/v1",
  apiKey: process.env.CHUTES_API_KEY, // sent as Authorization: Bearer
});

// Plain completion
const resp = await client.chat.completions.create({
  model: MODEL,
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: MODEL,
  messages: [{ role: "user", content: "Write a haiku about decentralized GPUs." }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
process.stdout.write("\n");
