const express = require("express");
const bodyParser = require("body-parser");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

let activeDomain = null;
let activeFolder = null;

const app = express();
app.use(bodyParser.json());
app.use(express.static("public"));

app.post("/run", (req, res) => {
    
    const { domain, url } = req.body;
    if (!domain) {
        return res.status(400).json({ error: "Domain required" });
    }
    activeDomain = domain;
    activeFolder = path.join(__dirname, "../data/Files", `${domain}_data`);
    const basePath = path.join(__dirname, "../data/Files");

    let args = ["-d", domain, "-t", "500"];
    if (url) args.push("-u", url);

    console.log("Starting Recon:", args.join(" "));

    // Step 1 – run bash recon
    const recon = spawn("./ip-range-recon.sh", args, { cwd: basePath });

    recon.stdout.on("data", d => console.log(d.toString()));
    recon.stderr.on("data", d => console.error(d.toString()));

    recon.on("close", () => {
        console.log("Recon finished.");

        const domainFolder = `${domain}_data`;
        const ipFile = `All_${domain}_IP_Range.txt`;
        const ipPath = `${domainFolder}/${ipFile}`;

        console.log("Starting Mongo receiver...");
        const mongoServer = spawn("python3", ["server.py"], { cwd: basePath });

        mongoServer.stdout.on("data", d => console.log("[Mongo]", d.toString()));
        mongoServer.stderr.on("data", d => console.error("[Mongo]", d.toString()));

        setTimeout(() => {
            console.log("Launching Scanner on:", ipPath);

            const scan = spawn("python3", ["scanner.py", ipPath], { cwd: basePath });

            scan.stdout.on("data", d => console.log("[SCAN]", d.toString()));
            scan.stderr.on("data", d => console.error("[SCAN]", d.toString()));

        }, 4000);

        res.json({ status: "Recon + Scan started", ip_file: ipPath });
    });

});

app.listen(3000, () => {
    console.log("Recon dashboard running at http://localhost:3000");
});


function cleanup() {
    if (activeFolder && fs.existsSync(activeFolder)) {
        console.log("🧹 Cleaning up:", activeFolder);
        fs.rmSync(activeFolder, { recursive: true, force: true });
    }
    process.exit();
}

// Ctrl+C
process.on("SIGINT", cleanup);

// kill, docker stop, etc
process.on("SIGTERM", cleanup);

// Node crash
process.on("exit", cleanup);
