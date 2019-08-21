class FetchService {
  url: string;

  constructor(url: string) {
    this.url = url;
  }

  get<T>(): Promise<T> {
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: T) => {
        return response;
      });
    });
  }
}

export default FetchService;
