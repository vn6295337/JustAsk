/**
 * JustAsk privacy and terms text. Keep in sync with the README privacy section
 * and with what the server and app actually do.
 */
export const PRIVACY_TITLE = 'JustAsk: Privacy and Terms';

export const PRIVACY_SECTIONS = [
  {
    heading: 'Who can use JustAsk',
    items: [
      'You must be 18 or older.',
      'JustAsk is not available in the EU, EEA, UK or Switzerland.',
    ],
  },
  {
    heading: 'Where your questions go',
    items: [
      'To answer you, our server sends your question to an AI company: Google (Gemini), Groq, or OpenRouter. OpenRouter passes it on to one of several AI providers.',
      'Google may use your questions to improve its products, and Google staff may read them.',
      'The other providers may keep your questions for a limited time, and some may use them to train AI.',
      'Do not type personal or private information, such as your name, address, health or money details, or passwords.',
    ],
  },
  {
    heading: 'What we keep',
    items: [
      'Our server does not save your questions, your answers or your internet address. Our hosting provider may keep basic technical logs for a short time.',
      'Your chat history is saved only on your phone, until you delete it in Settings.',
      'Cached answers are saved on your phone for 7 days so they load faster, then deleted.',
    ],
  },
  {
    heading: 'AI answers can be wrong',
    items: ['Check anything important before you rely on it.'],
  },
  {
    heading: 'Credits',
    items: ['IP Geolocation by DB-IP (db-ip.com), licensed under CC BY 4.0.'],
  },
];
