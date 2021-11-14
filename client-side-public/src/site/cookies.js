function areCookiesEnabled() {
    document.cookie = "__verify=1";
    let supportsCookies = document.cookie.length >= 1 && document.cookie.indexOf("__verify=1") !== -1;
    let thePast = new Date(2011, 9, 26);
    document.cookie = "__verify=1;expires=" + thePast.toUTCString();
    return supportsCookies;
}
function hasUserCookie() {
    return (document.cookie.length >= 1 && document.cookie.search(/\buser=/) !== -1);
}
export { areCookiesEnabled, hasUserCookie };
