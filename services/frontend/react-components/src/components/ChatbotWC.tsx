import React from "react";
import ChatbotWidget from "./ChatbotWidget";

const ChatbotWC: React.FC = () => {
  // visibility is internally controlled by authChanged events, nothing to pass here
  return <ChatbotWidget />;
};
export default ChatbotWC;
