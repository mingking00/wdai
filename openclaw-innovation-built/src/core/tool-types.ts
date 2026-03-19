export interface ToolCall {
  name: string;
  params: any;
  sessionId?: string;
}

export interface ToolResult {
  success?: boolean;
  result?: any;
  error?: string;
  metadata?: any;
}

export interface Tool {
  name: string;
  execute(params: any): Promise<ToolResult>;
}
