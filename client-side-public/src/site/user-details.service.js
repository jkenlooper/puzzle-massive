import FetchService from "./fetch.service";
const baseUrl = `${window.location.protocol}//${window.location.host}`;
const generateAnonymousLogin = new FetchService("/newapi/generate-anonymous-login/");
class UserDetailsService {
    constructor() {
        this.hasInitialized = false;
        this.listeners = new Map();
        this.userDetails = {
            dots: 0,
            score: 0,
            hasBit: false,
            bitBackground: "#ffffff00",
            isShareduser: true,
            loginAgain: false,
            user_puzzle_count: 0,
            puzzle_instance_count: 0,
            hasUserPuzzleSlots: false,
            hasAvailableUserPuzzleSlot: false,
            emptySlotCount: 0,
            puzzleInstanceCount: 0,
            name: "",
            nameApproved: false,
            nameRejected: false,
            email: "",
            emailVerified: false,
        };
        let hasLocalStorage = true;
        try {
            hasLocalStorage = !!window.localStorage;
        }
        catch (err) {
            hasLocalStorage = false;
        }
        if (!hasLocalStorage) {
            // User may have blocked the site from storing cookies and using
            // localStorage.
            // TODO: implement better system of showing alerts to the user.
            var message = "Cookies and localStorage are needed for this site.  Please enable them in your browser in order to continue.";
            var el = document.createElement("p");
            var body = document.querySelector("body");
            el.setAttribute("style", "font-size: 1.3em; font-weight: bold; border: 1px solid var(--color-accent); margin: 1em; padding: 10px; box-shadow: 3px 3px 0px 0px var(--color-dark); background-color: var(--color-light-accent);");
            el.style.maxWidth = Math.round(message.length * 0.765) + "em";
            el.classList.add("u-block");
            el.innerText = message;
            body.insertBefore(el, body.childNodes[0]);
            return;
        }
        this.currentUserId().then((currentUserId) => {
            // verify locally saved bit login with id that comes back.  If it is
            // different then login again.
            const localUserId = window.localStorage.getItem(UserDetailsService.localUserId);
            if (localUserId && localUserId != currentUserId) {
                if (window.localStorage.getItem(UserDetailsService.anonymousLoginName)) {
                    this.userDetails.loginAgain = true;
                }
            }
            this.updateUserDetails(currentUserId)
                .then(() => {
                this._broadcast();
            })
                .finally(() => {
                this.hasInitialized = true;
            });
        });
        document.addEventListener("userDetailsChange", this._onUserDetailsChange.bind(this));
    }
    generateAnonymousLogin() {
        return generateAnonymousLogin.get();
    }
    storeAnonymousLogin(anonymousLogin) {
        window.localStorage.setItem(UserDetailsService.anonymousLoginName, anonymousLogin);
        window.localStorage.setItem(UserDetailsService.localUserId, String(this.userDetails.id));
    }
    forgetAnonymousLogin() {
        window.localStorage.removeItem(UserDetailsService.anonymousLoginName);
        window.localStorage.removeItem(UserDetailsService.localUserId);
    }
    get anonymousLoginLink() {
        return `${baseUrl}${window.localStorage.getItem(UserDetailsService.anonymousLoginName) || ""}`;
    }
    currentUserId() {
        return fetch("/newapi/current-user-id/", {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
        }).then((response) => {
            if (!response.ok) {
                throw new Error(response.statusText);
            }
            return response.text();
        });
    }
    updateUserDetails(currentUserId = undefined) {
        if (!currentUserId) {
            return this.currentUserId().then(() => {
                return getUserDetails.call(this);
            });
        }
        else {
            return getUserDetails.call(this);
        }
        function getUserDetails() {
            // get the new user details from server
            return fetch("/newapi/user-details/", {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                },
            })
                .then((response) => {
                if (!response.ok) {
                    throw new Error(response.statusText);
                }
                return response.json().then((response) => {
                    return response;
                });
            })
                .then((userDetails) => {
                const hasBit = !!(userDetails.icon && userDetails.icon.trim());
                this.userDetails = Object.assign({
                    hasBit: hasBit,
                }, userDetails, {
                    loginAgain: this.userDetails.loginAgain,
                    hasUserPuzzleSlots: !!userDetails.user_puzzle_count,
                    hasAvailableUserPuzzleSlot: !!(userDetails.user_puzzle_count -
                        userDetails.puzzle_instance_count),
                    emptySlotCount: userDetails.user_puzzle_count -
                        userDetails.puzzle_instance_count,
                    puzzleInstanceCount: userDetails.puzzle_instance_count,
                });
                return;
            });
        }
    }
    _onUserDetailsChange( /*ev: Event*/) {
        this.updateUserDetails().then(() => {
            this._broadcast();
        });
    }
    _broadcast() {
        this.listeners.forEach((fn /*, id*/) => {
            fn();
        });
    }
    subscribe(fn, id) {
        //console.log("subscribe", fn, id);
        // Add the fn to listeners
        this.listeners.set(id, fn);
    }
    unsubscribe(id) {
        //console.log("unsubscribe", id);
        // remove fn from listeners
        this.listeners.delete(id);
    }
}
UserDetailsService.anonymousLoginName = "anonymous-login";
UserDetailsService.localUserId = "user-id";
const userDetailsService = new UserDetailsService();
export default userDetailsService;
