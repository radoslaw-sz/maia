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
  }[];
  assertions: {
    id: string;
    description: string;
    status: string;
    details: string;
  }[];
}
