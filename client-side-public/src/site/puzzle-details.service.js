import FetchService from "./fetch.service";
class PuzzleDetailsService {
    constructor() { }
    getPuzzleInstanceDetails(puzzleId) {
        const puzzleDetailsService = new FetchService(`/newapi/puzzle-instance-details/${puzzleId}/`);
        return puzzleDetailsService
            .get()
            .then((puzzleDetails) => {
            return puzzleDetails;
        });
    }
    patchPuzzleInstanceDetails(puzzleId, action) {
        const puzzleDetailsService = new FetchService(`/newapi/puzzle-instance-details/${puzzleId}/`);
        const data = {
            action: action,
        };
        return puzzleDetailsService
            .patch(data)
            .then((puzzleDetails) => {
            return puzzleDetails;
        });
    }
    getPuzzleOriginalDetails(puzzleId) {
        if (this._puzzleOriginalDetailsCache) {
            return Promise.resolve(this._puzzleOriginalDetailsCache);
        }
        const puzzleDetailsService = new FetchService(`/newapi/puzzle-original-details/${puzzleId}/`);
        this._puzzleOriginalDetailsCache = puzzleDetailsService
            .get()
            .then((puzzleDetails) => {
            return puzzleDetails;
        })
            .finally(() => {
            window.setTimeout(() => {
                // Invalidate the cache
                this._puzzleOriginalDetailsCache = undefined;
            }, 1000);
        });
        return this._puzzleOriginalDetailsCache;
    }
    patchPuzzleOriginalDetails(puzzleId, action) {
        const puzzleDetailsService = new FetchService(`/newapi/puzzle-original-details/${puzzleId}/`);
        const data = {
            action: action,
        };
        return puzzleDetailsService
            .patch(data)
            .then((puzzleDetails) => {
            return puzzleDetails;
        });
    }
}
export const puzzleDetailsService = new PuzzleDetailsService();
