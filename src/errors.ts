/** Every problem plotkit reports: a message, and a hint the model (or the user) can act on. */
export class PlotkitError extends Error {
  readonly hint: string;
  constructor(message: string, hint = "") {
    super(message);
    this.name = "PlotkitError";
    this.hint = hint;
  }
}
