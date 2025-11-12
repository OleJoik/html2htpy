import htpy as h
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from htpy.html2htpy import RuffFormatter, html2htpy
from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

app = FastAPI()
app.mount("/static", StaticFiles(directory="public"), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    return resp


@h.with_children
def page(children: h.Node):
    return h.html(data_bs_theme="dark")[
        h.head[
            h.meta(charset="utf-8"),
            h.link(
                rel="icon",
                type="image/png",
                sizes="32x32",
                href="static/favicon/favicon-32x32.png",
            ),
            h.link(
                rel="icon",
                type="image/png",
                sizes="16x16",
                href="static/favicon/favicon-16x16.png",
            ),
            h.title["html2htpy"],
            # --- Bootstrap ---
            h.link(
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css",
                rel="stylesheet",
                crossorigin="anonymous",
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"
            ),
            # --- Highlight.js ---
            h.link(rel="stylesheet", href="/static/css/pygments.css"),
            # --- htmx ---
            h.script(src="/static/js/htmx.min.js"),
            # --- CodeMirror (core + modes + dark theme) ---
            h.link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/lib/codemirror.min.css",
            ),
            h.link(
                href=" https://cdn.jsdelivr.net/npm/codemirror-one-dark-theme@1.1.1/one-dark.min.css ",
                rel="stylesheet",
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/lib/codemirror.min.js"
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/addon/display/placeholder.min.js"
            ),
            # 🔥 Syntax highlighting modes (required for htmlmixed)
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/mode/xml/xml.min.js"
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/mode/javascript/javascript.min.js"
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/mode/css/css.min.js"
            ),
            h.script(
                src="https://cdn.jsdelivr.net/npm/codemirror@5.65.15/mode/htmlmixed/htmlmixed.min.js"
            ),
            # --- Styling ---
            h.style[
                """
                .CodeMirror {
                    height: 100% !important;
                    background-color: transparent !important;
                    color: var(--bs-body-color) !important;
                    border: 1px solid var(--bs-border-color);
                    border-radius: var(--bs-border-radius);
                    padding: 0.5rem;
                }
                .CodeMirror-gutters {
                    background-color: transparent !important;
                    border: none !important;
                }
                pre#converted-htpy {
                    position: relative;
                    border: 1px solid var(--bs-border-color);
                    border-radius: var(--bs-border-radius);
                    background-color: transparent !important;
                    font-size: 1rem !important; /* matches Bootstrap body text size */
                    overflow: auto;
                }

                .CodeMirror, pre#converted-htpy code {
                  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
                  font-size: 1rem !important;
                  line-height: 1.5 !important;
                }

                .copy-btn {
                    position: absolute;
                    top: 0.25rem;
                    right: 0.25rem;
                    z-index: 10;
                    opacity: 0.6;
                    transition: opacity 0.15s ease-in-out;
                }
                .copy-btn:hover {
                    opacity: 1;
                }
                """
            ],
        ],
        h.body[
            h.main(
                class_="container-fluid d-flex flex-column min-vh-100 justify-content-center pb-4"
            )[children],
            # --- Inline JS (minimal, clean) ---
            h.script[
                Markup(
                    """
                    document.addEventListener("DOMContentLoaded", () => {
                        const textarea = document.querySelector("#editor");

                        // Setup CodeMirror with syntax highlighting
                        const editor = CodeMirror.fromTextArea(textarea, {
                            mode: "htmlmixed",
                            lineNumbers: false,
                            theme: "one-dark",
                            tabSize: 2,
                            placeholder: "<!-- Type or paste your raw HTML here... -->",
                        });
                        editor.setSize("100%", "100%");
                        editor.on("change", () => {
                            textarea.value = editor.getValue();
                            htmx.trigger(textarea, "change");
                        });

                        const init = () => {
                            document.querySelectorAll(".copy-btn").forEach(btn => {
                                btn.onclick = async () => {
                                    const code = btn.parentElement.querySelector("code");
                                    await navigator.clipboard.writeText(code.textContent);
                                    btn.textContent = "Copied!";
                                    setTimeout(() => btn.textContent = "Copy", 1500);
                                };
                            });
                        };
                        init();
                        document.body.addEventListener("htmx:afterSettle", init);
                    });
                    """
                )
            ],
        ],
    ]


@app.get("/")
def root():
    return HTMLResponse(
        page[
            h.h1(class_="text-center mb-4 mt-4")["html2htpy"],
            h.div(
                class_="row g-3 flex-grow-1 justify-content-center align-items-stretch"
            )[
                # --- Left: Code editor ---
                h.div(class_="col-12 col-xl-6 d-flex")[
                    h.label(for_="editor", class_="visually-hidden")["Input HTML"],
                    h.textarea(
                        id="editor",
                        name="input",
                        class_="form-control flex-fill h-100 w-100",
                        hx_post="/",
                        hx_swap="outerHTML",
                        hx_target="#converted-htpy",
                        hx_trigger="load, change delay:300ms",
                        placeholder="raw html",
                        spellcheck="false",
                        autocapitalize="off",
                        autocomplete="off",
                    ),
                ],
                # --- Right: Output code box with floating Copy button ---
                h.div(class_="col-12 col-xl-6 d-flex position-relative")[
                    h.pre(
                        id="converted-htpy",
                        class_="flex-fill h-100 position-relative",
                    )[
                        h.button(
                            type="button",
                            class_="btn btn-sm btn-outline-secondary copy-btn",
                        )["Copy"],
                        h.code(
                            class_="bg-dark p-2 rounded w-100 h-100 d-block highlighted",
                        )[h.span(class_="c")["# Generated htpy code will appear here"]],
                    ]
                ],
            ],
        ]
    )


MAX_BYTES = 500_000


def highlight_python(source: str) -> str:
    formatter = HtmlFormatter(nowrap=True)
    return highlight(source, PythonLexer(), formatter)


@app.post("/")
def convert(input: str = Form(default="")):
    if not input.strip():
        python_response = h.span(class_="c")["# Generated htpy code will appear here"]

    else:
        try:
            h2py = html2htpy(
                input,
                formatter=RuffFormatter(),
                import_mode="h",
                shorthand_id_class=False,
            )

            python_response = highlight_python(h2py)
        except Exception as e:
            python_response = str(e)

    return HTMLResponse(
        str(
            h.pre(
                id="converted-htpy",
                class_="flex-fill h-100 position-relative",
            )[
                h.button(
                    type="button",
                    class_="btn btn-sm btn-outline-secondary copy-btn",
                )["Copy"],
                Markup(
                    f'<code class="bg-dark p-2 rounded w-100 h-100 d-block highlighted">{python_response}</code>'
                ),
            ]
        )
    )
