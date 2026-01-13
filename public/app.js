function run() {
    let domain = document.getElementById("domain").value;
    let bgp = document.getElementById("bgp").value;

    fetch("/run", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({domain, url: bgp})
    })
    .then(r => r.json())
    .then(d => alert(JSON.stringify(d)))
}
