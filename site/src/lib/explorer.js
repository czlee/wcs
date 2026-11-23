/**
 * How the layout (whose footer is on every page) opens a dialog of the explorer: set by the
 * explorer while it's on the page.
 * @type {{open: ((dialog: import('./view.js').Dialog) => void) | null}}
 */
export const explorer = { open: null };
