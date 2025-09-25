# Custom Tools

> Build and integrate custom tools to extend Claude Code SDK functionality

Custom tools allow you to extend Claude Code's capabilities with your own functionality through in-process MCP servers, enabling Claude to interact with external services, APIs, or perform specialized operations.

## Creating Custom Tools

Use the `createSdkMcpServer` and `tool` helper functions to define type-safe custom tools:

<CodeGroup>
  ```typescript TypeScript
  import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-code";
  import { z } from "zod";

// Create an SDK MCP server with custom tools
const customServer = createSdkMcpServer({
name: "my-custom-tools",
version: "1.0.0",
tools: [
tool(
"get_weather",
"Get current weather for a location",
{
location: z.string().describe("City name or coordinates"),
units: z.enum(["celsius", "fahrenheit"]).default("celsius").describe("Temperature units")
},
async (args) => {
// Call weather API
const response = await fetch(
`https://api.weather.com/v1/current?q=${args.location}&units=${args.units}`
);
const data = await response.json();

          return {
            content: [{
              type: "text",
              text: `Temperature: ${data.temp}°\nConditions: ${data.conditions}\nHumidity: ${data.humidity}%`
            }]
          };
        }
      )
    ]

});

````

```python Python
from claude_code_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeCodeOptions
from typing import Any
import aiohttp

# Define a custom tool using the @tool decorator
@tool("get_weather", "Get current weather for a location", {"location": str, "units": str})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    # Call weather API
    units = args.get('units', 'celsius')
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.weather.com/v1/current?q={args['location']}&units={units}"
        ) as response:
            data = await response.json()

    return {
        "content": [{
            "type": "text",
            "text": f"Temperature: {data['temp']}°\nConditions: {data['conditions']}\nHumidity: {data['humidity']}%"
        }]
    }

# Create an SDK MCP server with the custom tool
custom_server = create_sdk_mcp_server(
    name="my-custom-tools",
    version="1.0.0",
    tools=[get_weather]  # Pass the decorated function
)
````

</CodeGroup>

## Using Custom Tools

Pass the custom server to the `query` function via the `mcpServers` option as a dictionary/object.

<Note>
  **Important:** Custom MCP tools require streaming input mode. You must use an async generator/iterable for the `prompt` parameter - a simple string will not work with MCP servers.
</Note>

### Tool Name Format

When MCP tools are exposed to Claude, their names follow a specific format:

- Pattern: `mcp__{server_name}__{tool_name}`
- Example: A tool named `get_weather` in server `my-custom-tools` becomes `mcp__my-custom-tools__get_weather`

### Configuring Allowed Tools

You can control which tools Claude can use via the `allowedTools` option:

<CodeGroup>
  ```typescript TypeScript
  import { query } from "@anthropic-ai/claude-code";

// Use the custom tools in your query with streaming input
async function\* generateMessages() {
yield {
type: "user" as const,
message: {
role: "user" as const,
content: "What's the weather in San Francisco?"
}
};
}

for await (const message of query({
prompt: generateMessages(), // Use async generator for streaming input
options: {
mcpServers: {
"my-custom-tools": customServer // Pass as object/dictionary, not array
},
// Optionally specify which tools Claude can use
allowedTools: [
"mcp__my-custom-tools__get_weather", // Allow the weather tool
// Add other tools as needed
],
maxTurns: 3
}
})) {
if (message.type === "result" && message.subtype === "success") {
console.log(message.result);
}
}

````

```python Python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
import asyncio

# Use the custom tools with Claude
options = ClaudeCodeOptions(
    mcp_servers={"my-custom-tools": custom_server},
    allowed_tools=[
        "mcp__my-custom-tools__get_weather",  # Allow the weather tool
        # Add other tools as needed
    ]
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's the weather in San Francisco?")

        # Extract and print response
        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
````

</CodeGroup>

### Multiple Tools Example

When your MCP server has multiple tools, you can selectively allow them:

<CodeGroup>
  ```typescript TypeScript
  const multiToolServer = createSdkMcpServer({
    name: "utilities",
    version: "1.0.0",
    tools: [
      tool("calculate", "Perform calculations", { /* ... */ }, async (args) => { /* ... */ }),
      tool("translate", "Translate text", { /* ... */ }, async (args) => { /* ... */ }),
      tool("search_web", "Search the web", { /* ... */ }, async (args) => { /* ... */ })
    ]
  });

// Allow only specific tools with streaming input
async function\* generateMessages() {
yield {
type: "user" as const,
message: {
role: "user" as const,
content: "Calculate 5 + 3 and translate 'hello' to Spanish"
}
};
}

for await (const message of query({
prompt: generateMessages(), // Use async generator for streaming input
options: {
mcpServers: {
utilities: multiToolServer
},
allowedTools: [
"mcp__utilities__calculate", // Allow calculator
"mcp__utilities__translate", // Allow translator
// "mcp__utilities__search_web" is NOT allowed
]
}
})) {
// Process messages
}

````

```python Python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, tool, create_sdk_mcp_server
from typing import Any
import asyncio

# Define multiple tools using the @tool decorator
@tool("calculate", "Perform calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    result = eval(args["expression"])  # Use safe eval in production
    return {"content": [{"type": "text", "text": f"Result: {result}"}]}

@tool("translate", "Translate text", {"text": str, "target_lang": str})
async def translate(args: dict[str, Any]) -> dict[str, Any]:
    # Translation logic here
    return {"content": [{"type": "text", "text": f"Translated: {args['text']}"}]}

@tool("search_web", "Search the web", {"query": str})
async def search_web(args: dict[str, Any]) -> dict[str, Any]:
    # Search logic here
    return {"content": [{"type": "text", "text": f"Search results for: {args['query']}"}]}

multi_tool_server = create_sdk_mcp_server(
    name="utilities",
    version="1.0.0",
    tools=[calculate, translate, search_web]  # Pass decorated functions
)

# Allow only specific tools with streaming input
async def message_generator():
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": "Calculate 5 + 3 and translate 'hello' to Spanish"
        }
    }

<<<<<<< Updated upstream
async for message in query(
    prompt=message_generator(),  # Use async generator for streaming input
    options=ClaudeCodeOptions(
        mcp_servers={"utilities": multi_tool_server},
        allowed_tools=[
            "mcp__utilities__calculate",   # Allow calculator
            "mcp__utilities__translate",   # Allow translator
            # "mcp__utilities__search_web" is NOT allowed
        ]
    )
):
    if hasattr(message, 'result'):
        print(message.result)
=======
async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Calculate 5 + 3 and translate 'hello' to Spanish")

        # Process messages
        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
>>>>>>> Stashed changes
````

</CodeGroup>

## Type Safety with Python

The `@tool` decorator supports various schema definition approaches for type safety:

<CodeGroup>
  ```typescript TypeScript
  import { z } from "zod";

tool(
"process_data",
"Process structured data with type safety",
{
// Zod schema defines both runtime validation and TypeScript types
data: z.object({
name: z.string(),
age: z.number().min(0).max(150),
email: z.string().email(),
preferences: z.array(z.string()).optional()
}),
format: z.enum(["json", "csv", "xml"]).default("json")
},
async (args) => {
// args is fully typed based on the schema
// TypeScript knows: args.data.name is string, args.data.age is number, etc.
console.log(`Processing ${args.data.name}'s data as ${args.format}`);

      // Your processing logic here
      return {
        content: [{
          type: "text",
          text: `Processed data for ${args.data.name}`
        }]
      };
    }

)

````

```python Python
from typing import Any

# Simple type mapping - recommended for most cases
@tool(
    "process_data",
    "Process structured data with type safety",
    {
        "name": str,
        "age": int,
        "email": str,
        "preferences": list  # Optional parameters can be handled in the function
    }
)
async def process_data(args: dict[str, Any]) -> dict[str, Any]:
    # Access arguments with type hints for IDE support
    name = args["name"]
    age = args["age"]
    email = args["email"]
    preferences = args.get("preferences", [])

    print(f"Processing {name}'s data (age: {age})")

    return {
        "content": [{
            "type": "text",
            "text": f"Processed data for {name}"
        }]
    }

# For more complex schemas, you can use JSON Schema format
@tool(
    "advanced_process",
    "Process data with advanced validation",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "email": {"type": "string", "format": "email"},
            "format": {"type": "string", "enum": ["json", "csv", "xml"], "default": "json"}
        },
        "required": ["name", "age", "email"]
    }
)
async def advanced_process(args: dict[str, Any]) -> dict[str, Any]:
    # Process with advanced schema validation
    return {
        "content": [{
            "type": "text",
            "text": f"Advanced processing for {args['name']}"
        }]
    }
````

</CodeGroup>

## Error Handling

Handle errors gracefully to provide meaningful feedback:

<CodeGroup>
  ```typescript TypeScript
  tool(
    "fetch_data",
    "Fetch data from an API",
    {
      endpoint: z.string().url().describe("API endpoint URL")
    },
    async (args) => {
      try {
        const response = await fetch(args.endpoint);

        if (!response.ok) {
          return {
            content: [{
              type: "text",
              text: `API error: ${response.status} ${response.statusText}`
            }]
          };
        }

        const data = await response.json();
        return {
          content: [{
            type: "text",
            text: JSON.stringify(data, null, 2)
          }]
        };
      } catch (error) {
        return {
          content: [{
            type: "text",
            text: `Failed to fetch data: ${error.message}`
          }]
        };
      }
    }

)

````

```python Python
import json
import aiohttp
from typing import Any

@tool(
    "fetch_data",
    "Fetch data from an API",
    {"endpoint": str}  # Simple schema
)
async def fetch_data(args: dict[str, Any]) -> dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(args["endpoint"]) as response:
                if response.status != 200:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"API error: {response.status} {response.reason}"
                        }]
                    }

                data = await response.json()
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }]
                }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to fetch data: {str(e)}"
            }]
        }
````

</CodeGroup>

## Example Tools

### Database Query Tool

<CodeGroup>
  ```typescript TypeScript
  const databaseServer = createSdkMcpServer({
    name: "database-tools",
    version: "1.0.0",
    tools: [
      tool(
        "query_database",
        "Execute a database query",
        {
          query: z.string().describe("SQL query to execute"),
          params: z.array(z.any()).optional().describe("Query parameters")
        },
        async (args) => {
          const results = await db.query(args.query, args.params || []);
          return {
            content: [{
              type: "text",
              text: `Found ${results.length} rows:\n${JSON.stringify(results, null, 2)}`
            }]
          };
        }
      )
    ]
  });
  ```

```python Python
from typing import Any
import json

@tool(
    "query_database",
    "Execute a database query",
    {"query": str, "params": list}  # Simple schema with list type
)
async def query_database(args: dict[str, Any]) -> dict[str, Any]:
    results = await db.query(args["query"], args.get("params", []))
    return {
        "content": [{
            "type": "text",
            "text": f"Found {len(results)} rows:\n{json.dumps(results, indent=2)}"
        }]
    }

database_server = create_sdk_mcp_server(
    name="database-tools",
    version="1.0.0",
    tools=[query_database]  # Pass the decorated function
)
```

</CodeGroup>

### API Gateway Tool

<CodeGroup>
  ```typescript TypeScript
  const apiGatewayServer = createSdkMcpServer({
    name: "api-gateway",
    version: "1.0.0",
    tools: [
      tool(
        "api_request",
        "Make authenticated API requests to external services",
        {
          service: z.enum(["stripe", "github", "openai", "slack"]).describe("Service to call"),
          endpoint: z.string().describe("API endpoint path"),
          method: z.enum(["GET", "POST", "PUT", "DELETE"]).describe("HTTP method"),
          body: z.record(z.any()).optional().describe("Request body"),
          query: z.record(z.string()).optional().describe("Query parameters")
        },
        async (args) => {
          const config = {
            stripe: { baseUrl: "https://api.stripe.com/v1", key: process.env.STRIPE_KEY },
            github: { baseUrl: "https://api.github.com", key: process.env.GITHUB_TOKEN },
            openai: { baseUrl: "https://api.openai.com/v1", key: process.env.OPENAI_KEY },
            slack: { baseUrl: "https://slack.com/api", key: process.env.SLACK_TOKEN }
          };

          const { baseUrl, key } = config[args.service];
          const url = new URL(`${baseUrl}${args.endpoint}`);

          if (args.query) {
            Object.entries(args.query).forEach(([k, v]) => url.searchParams.set(k, v));
          }

          const response = await fetch(url, {
            method: args.method,
            headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
            body: args.body ? JSON.stringify(args.body) : undefined
          });

          const data = await response.json();
          return {
            content: [{
              type: "text",
              text: JSON.stringify(data, null, 2)
            }]
          };
        }
      )
    ]

});

````

```python Python
import os
import json
import aiohttp
from typing import Any

# For complex schemas with enums, use JSON Schema format
@tool(
    "api_request",
    "Make authenticated API requests to external services",
    {
        "type": "object",
        "properties": {
            "service": {"type": "string", "enum": ["stripe", "github", "openai", "slack"]},
            "endpoint": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "body": {"type": "object"},
            "query": {"type": "object"}
        },
        "required": ["service", "endpoint", "method"]
    }
)
async def api_request(args: dict[str, Any]) -> dict[str, Any]:
    config = {
        "stripe": {"base_url": "https://api.stripe.com/v1", "key": os.environ["STRIPE_KEY"]},
        "github": {"base_url": "https://api.github.com", "key": os.environ["GITHUB_TOKEN"]},
        "openai": {"base_url": "https://api.openai.com/v1", "key": os.environ["OPENAI_KEY"]},
        "slack": {"base_url": "https://slack.com/api", "key": os.environ["SLACK_TOKEN"]}
    }

    service_config = config[args["service"]]
    url = f"{service_config['base_url']}{args['endpoint']}"

    if args.get("query"):
        params = "&".join([f"{k}={v}" for k, v in args["query"].items()])
        url += f"?{params}"

    headers = {"Authorization": f"Bearer {service_config['key']}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.request(
            args["method"], url, headers=headers, json=args.get("body")
        ) as response:
            data = await response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(data, indent=2)
                }]
            }

api_gateway_server = create_sdk_mcp_server(
    name="api-gateway",
    version="1.0.0",
    tools=[api_request]  # Pass the decorated function
)
````

</CodeGroup>

### Calculator Tool

<CodeGroup>
  ```typescript TypeScript
  const calculatorServer = createSdkMcpServer({
    name: "calculator",
    version: "1.0.0",
    tools: [
      tool(
        "calculate",
        "Perform mathematical calculations",
        {
          expression: z.string().describe("Mathematical expression to evaluate"),
          precision: z.number().optional().default(2).describe("Decimal precision")
        },
        async (args) => {
          try {
            // Use a safe math evaluation library in production
            const result = eval(args.expression); // Example only!
            const formatted = Number(result).toFixed(args.precision);

            return {
              content: [{
                type: "text",
                text: `${args.expression} = ${formatted}`
              }]
            };
          } catch (error) {
            return {
              content: [{
                type: "text",
                text: `Error: Invalid expression - ${error.message}`
              }]
            };
          }
        }
      ),
      tool(
        "compound_interest",
        "Calculate compound interest for an investment",
        {
          principal: z.number().positive().describe("Initial investment amount"),
          rate: z.number().describe("Annual interest rate (as decimal, e.g., 0.05 for 5%)"),
          time: z.number().positive().describe("Investment period in years"),
          n: z.number().positive().default(12).describe("Compounding frequency per year")
        },
        async (args) => {
          const amount = args.principal * Math.pow(1 + args.rate / args.n, args.n * args.time);
          const interest = amount - args.principal;

          return {
            content: [{
              type: "text",
              text: `Investment Analysis:\n` +
                    `Principal: $${args.principal.toFixed(2)}\n` +
                    `Rate: ${(args.rate * 100).toFixed(2)}%\n` +
                    `Time: ${args.time} years\n` +
                    `Compounding: ${args.n} times per year\n\n` +
                    `Final Amount: $${amount.toFixed(2)}\n` +
                    `Interest Earned: $${interest.toFixed(2)}\n` +
                    `Return: ${((interest / args.principal) * 100).toFixed(2)}%`
            }]
          };
        }
      )
    ]

});

````

```python Python
import math
from typing import Any

@tool(
    "calculate",
    "Perform mathematical calculations",
    {"expression": str, "precision": int}  # Simple schema
)
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        # Use a safe math evaluation library in production
        result = eval(args["expression"], {"__builtins__": {}})
        precision = args.get("precision", 2)
        formatted = round(result, precision)

        return {
            "content": [{
                "type": "text",
                "text": f"{args['expression']} = {formatted}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Invalid expression - {str(e)}"
            }]
        }

@tool(
    "compound_interest",
    "Calculate compound interest for an investment",
    {"principal": float, "rate": float, "time": float, "n": int}
)
async def compound_interest(args: dict[str, Any]) -> dict[str, Any]:
    principal = args["principal"]
    rate = args["rate"]
    time = args["time"]
    n = args.get("n", 12)

    amount = principal * (1 + rate / n) ** (n * time)
    interest = amount - principal

    return {
        "content": [{
            "type": "text",
            "text": f"""Investment Analysis:
Principal: ${principal:.2f}
Rate: {rate * 100:.2f}%
Time: {time} years
Compounding: {n} times per year

Final Amount: ${amount:.2f}
Interest Earned: ${interest:.2f}
Return: {(interest / principal) * 100:.2f}%"""
        }]
    }

calculator_server = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[calculate, compound_interest]  # Pass decorated functions
)
````

</CodeGroup>

## Related Documentation

- [TypeScript SDK Reference](/en/docs/claude-code/sdk/typescript)
- [Python SDK Reference](/en/docs/claude-code/sdk/python)
- [MCP Documentation](https://modelcontextprotocol.io)
- [SDK Configuration](/en/docs/claude-code/sdk/sdk-configuration)
