type UserDetailsCallback = () => any;

interface UserDetailsData {
  login: string;
  icon: string;
  score: number;
  dots: number;
  id: string;
  cookie_expires: string;
  bit_expired: boolean;
}

class UserDetailsService {
  hasInitialized: boolean = false;
  listeners: Map<string, UserDetailsCallback> = new Map();
  userDetails: UserDetailsData = {
    score: 0,
    dots: 0,
    login: "something",
    id: "2",
    icon: "tree",
    cookie_expires: "somethingasdf",
    bit_expired: false,
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
