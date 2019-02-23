type UserDetailsCallback = () => any;

interface UserDetailsData {
  bit_expired?: boolean;
  cookie_expires?: string;
  dots: number;
  icon?: string;
  id?: number;
  login?: string;
  score: number;
}

class UserDetailsService {
  hasInitialized: boolean = false;
  listeners: Map<string, UserDetailsCallback> = new Map();
  userDetails: UserDetailsData = {
    dots: 0,
    score: 0,
  };

  constructor() {
    this.updateUserDetails()
      .then(() => {
        this._broadcast();
      })
      .finally(() => {
        this.hasInitialized = true;
      });
    document.addEventListener(
      "userDetailsChange",
      this._onUserDetailsChange.bind(this)
    );
  }

  updateUserDetails(): Promise<void> {
    return fetch("/newapi/current-user-id/")
      .then((response: Response) => {
        if (!response.ok) {
          throw new Error(response.statusText);
        }
      })
      .then(() => {
        // get the new user details from server
        return fetch("/newapi/user-details/")
          .then((response: Response) => {
            if (!response.ok) {
              throw new Error(response.statusText);
            }
            return response.json().then((response: UserDetailsData) => {
              return response;
            });
          })
          .then((userDetails) => {
            this.userDetails = userDetails;
          });
      });
  }

  _onUserDetailsChange(/*ev: Event*/) {
    this.updateUserDetails().then(() => {
      this._broadcast();
    });
  }

  _broadcast() {
    this.listeners.forEach((fn /*, id*/) => {
      fn();
    });
  }

  subscribe(fn: UserDetailsCallback, id: string) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }

  unsubscribe(id: string) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

const userDetailsService = new UserDetailsService();
export default userDetailsService;
