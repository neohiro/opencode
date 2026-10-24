import { Effect, Schema } from "effect"
import { createLocalProviderPlugin } from "./local"

// Schema for OpenAI-compatible /v1/models response
const OpenAIModel = Schema.Struct({
  id: Schema.String,
  object: Schema.Literal("model"),
  created: Schema.Number,
  owned_by: Schema.String,
  permission: Schema.Array(Schema.Unknown).pipe(Schema.optional),
  root: Schema.String.pipe(Schema.optional),
  parent: Schema.String.pipe(Schema.optional),
)

const Response = Schema.Struct({
  object: Schema.Literal("list"),
  data: Schema.Array(OpenAIModel),
)

export const make = createLocalProviderPlugin({
  id: "opencode.provider.local",
  providerID: "local",
  name: "Local",
  origin: "http://127.0.0.1:1234",
  stripPathSuffix: /\/v1$/,
  discover: (client) =>
    Effect.gen(function* () {
      const response = yield* client.getJson("/models", Response)
      return response.data
        .filter((model) => model.id.length > 0)
        .toSorted((a, b) => a.id.localeCompare(b.id))
    }),
  model: (item) => ({
    id: item.id,
    name: item.id,
    family: undefined,
    tools: undefined,
    vision: undefined,
    context: undefined,
  }),
})

export const LocalPlugin = make()
