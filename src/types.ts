// Shared shapes between the modules of plotkit-ts.

/** A file the host hands over: its name as the model sees it (may contain folders, e.g. "data/run_log.xlsx") and
 *  its bytes. plotkit never reads paths. */
export interface InputFile {
  name: string;
  bytes: Uint8Array;
}

/** A raw cell as the reader returns it (openpyxl / the text parser): numbers, text, booleans, empty, or a date.
 *  Dates are {date: "YYYY-MM-DDTHH:MM:SS"} (naive, as openpyxl gives them). Integers and floats are both numbers;
 *  where Python's int/float distinction shows (str(), labels), the module tracks it itself. */
export type Cell = number | string | boolean | null | { date: string };

/** {sheet name: rows of cells} and the decimal mark, as plotkit.core.read_tables returns them. */
export interface Tables {
  sheets: Map<string, Cell[][]>;
  decimal: string;
}

/** A column dtype as pandas had it: float64 (NaN for missing), int64, bool, datetime64 (NaT for missing), object
 *  (text and mixed; null for missing). */
export type Dtype = "float" | "int" | "bool" | "datetime" | "object";

/** A loaded chart table (plotkit.charts.load_frame): columns in order (names can repeat), one array per column.
 *  float/int columns hold numbers (NaN = missing); datetime columns hold epoch milliseconds of the naive date-time
 *  read as UTC (NaN = NaT); object columns hold strings, numbers, booleans or null. letters maps a column name to
 *  its spreadsheet letter (df.attrs["letters"]). */
export interface Frame {
  columns: string[];
  dtypes: Dtype[];
  data: (number | string | boolean | null)[][];
  letters: Record<string, string>;
}

/** A host-supplied sandbox for the data hatch: runs a JavaScript program (plotkit builds it) on JSON input and
 *  returns its JSON result. In KetchupE this is the QuickJS sandbox (electron/excel/sandbox.ts). */
export type RunCode = (program: string, input: unknown, signal?: AbortSignal) => Promise<unknown>;
