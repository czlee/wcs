// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		interface PageState {
			/** How many history entries back the explorer without a dialog is (ExplorePage.svelte). */
			depth?: number;
		}
		// interface Platform {}
	}
}

export {};
