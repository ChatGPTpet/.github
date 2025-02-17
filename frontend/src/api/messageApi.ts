import { Message } from '../models/Message';
import Request from './Request';

export const createSearchMessage = (message: Message): Promise<Message> => {
  return Request({
    url: '/api/messages/search',
    method: 'POST',
    data: message
  });
};

export const createChatGPTMessage = (
  message: Message,
  demo?: boolean
): Promise<Message> => {
  const baseUrl = '/api/messages/chatgpt';
  const url = demo ? `${baseUrl}?demo=true` : baseUrl;

  return Request({
    url: url,
    method: 'POST',
    data: message
  });
};

export const createWebSearchMessage = (
  message: Message,
  demo?: boolean
): Promise<Message> => {
  const baseUrl = '/api/messages/websearch';
  const url = demo ? `${baseUrl}?demo=true` : baseUrl;

  return Request({
    url: url,
    method: 'POST',
    data: message
  });
};
