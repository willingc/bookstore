const child_process = require("child_process");
const { randomBytes } = require("crypto");
const path = require("path");

global.XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;

const { ajax } = require("rxjs/ajax");

const rxJupyter = require("rx-jupyter");

console.log("running bookstore integration tests");

async function genToken(byteLength = 32) {
  return new Promise((resolve, reject) => {
    randomBytes(byteLength, (err, buffer) => {
      if (err) {
        reject(err);
        return;
      }

      resolve(buffer.toString("hex"));
    });
  });
}

const sleep = timeout =>
  new Promise((resolve, reject) => setTimeout(resolve, timeout));

const main = async () => {
  const jupyterToken = await genToken();
  const jupyterPort = 9988;

  const jupyterEndpoint = `http://127.0.0.1:${jupyterPort}`;

  console.log("launching in ", __dirname);

  const jupyter = child_process.spawn(
    "jupyter",
    [
      "notebook",
      "--no-browser",
      `--NotebookApp.token=${jupyterToken}`,
      `--NotebookApp.disable_check_xsrf=True`,
      `--port=${jupyterPort}`
    ],
    { cwd: __dirname }
  );

  ////// Refactor me later, streams are a bit messy with async await
  // Check to see that jupyter is up
  let jupyterUp = false;

  jupyter.stdout.on("data", data => {
    const s = data.toString();
    console.log(s);
  });
  jupyter.stderr.on("data", data => {
    const s = data.toString();

    console.error(s);
    if (s.includes("Jupyter Notebook is running at")) {
      jupyterUp = true;
    }
  });
  jupyter.stdout.on("end", data => console.log("DONE WITH JUPYTER"));

  jupyter.on("exit", code => {
    if (code != 0) {
      // Jupyter exited badly
      console.error("jupyter errored", code);
      process.exit(code);
    }
  });

  await sleep(3000);

  if (!jupyterUp) {
    console.log("jupyter has not come up after 3 seconds, waiting 3 more");
    await sleep(3000);

    if (!jupyterUp) {
      console.log("jupyter has not come up after 6 seconds, bailing");
      process.exit(1);
    }
  }

  const xhr = await ajax({
    url: `${jupyterEndpoint}/api/contents/ci-local-writeout.ipynb`,
    responseType: "json",
    createXHR: () => new XMLHttpRequest(),
    method: "PUT",
    body: {
      type: "notebook",
      content: {
        cells: [
          {
            cell_type: "code",
            execution_count: null,
            metadata: {},
            outputs: [],
            source: ["import this"]
          }
        ],
        metadata: {
          kernelspec: {
            display_name: "Python 3",
            language: "python",
            name: "python3"
          },
          language_info: {
            codemirror_mode: {
              name: "ipython",
              version: 3
            },
            file_extension: ".py",
            mimetype: "text/x-python",
            name: "python",
            nbconvert_exporter: "python",
            pygments_lexer: "ipython3",
            version: "3.7.0"
          }
        },
        nbformat: 4,
        nbformat_minor: 2
      }
    },
    headers: {
      "Content-Type": "application/json",
      Authorization: `token ${jupyterToken}`
    }
  }).toPromise();

  console.log(xhr.response);

  jupyter.kill();

  process.exit(0);

  // Jupyter now up
};

main();
