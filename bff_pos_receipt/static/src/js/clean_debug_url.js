/** @odoo-module **/
if (window.location.pathname.startsWith('/pos/ui') && window.location.search.includes('debug=')) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete('debug');
    const newSearch = urlParams.toString();
    const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
    window.location.replace(newUrl);
}
