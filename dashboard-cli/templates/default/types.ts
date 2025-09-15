export interface RequirementResult {
  requirement: string;
  verdict: string;
  score: number;
  reasoning: string;
}

export interface JudgeResult {
  verdict: string;
  score: number;
  reasoning: string;
  requirements: RequirementResult[];
}


export interface TestReport {
  test_id: string;
  test_name: string;
  start_time: string;
  end_time: string;
  status: string;
  participants: {
    id: string;
    name: string;
    type: string;
    metadata: any;
  }[];
  sessions: {
    id: string;
    participants: string[];
    messages: {
      content: string;
      sender: string;
      sender_type: string;
      receiver?: string,
      receiver_type?: string,
      timestamp: string;
      metadata: any;
      message_id: string;
    }[];
    assertions: {
      id: string;
      assertion_name: string;
      description?: string;
      status: string;
      metadata: any
    }[];
    validators: {
      name: string;
      status: string;
      details: {
        error: string;
        traceback: string;
      };
    }[];
    judge_result: JudgeResult
  }[];
}