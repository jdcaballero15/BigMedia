/** Mensajes de error de un campo, tal como los devuelve la API. */
export function FieldErrors({ messages }: { messages?: string[] }) {
  return messages?.map((message) => (
    <small className="error" key={message}>
      {message}
    </small>
  ))
}
