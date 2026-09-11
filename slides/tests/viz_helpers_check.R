# Asserts the number-formatting contract of R/viz.R and of its copy in
# slides/R/nexer-ggplot.R. Run by tests/test_viz_templates.py; exits non-zero
# on the first broken expectation.
check_formatters <- function(path) {
  env <- new.env()
  sys.source(path, envir = env)
  short <- env$label_short()
  got <- short(c(0, 999, 1000, 25000, 999999, 1e6, 1.25e6, 5e6, 1e9, 1.2e9, -3500, -1.2e6, NA))
  want <- c("0", "999", "1,000", "25,000", "999,999", "1m", "1.2m", "5m", "1bn", "1.2bn",
            "-3,500", "-1.2m", NA)
  if (!identical(got, want)) {
    stop(path, ": label_short() gave ", paste(got, collapse = " | "),
         "\n  wanted ", paste(want, collapse = " | "))
  }
  got <- env$label_short(accuracy = 0.1)(c(0.5, 1234.56, 2.34e6))
  want <- c("0.5", "1,234.6", "2.3m")
  if (!identical(got, want)) {
    stop(path, ": label_short(accuracy = 0.1) gave ", paste(got, collapse = " | "))
  }
  got <- c(env$label_pct()(0.12), env$label_pct(accuracy = 0.1)(0.125), env$label_pct(scale = 1)(12))
  want <- c("12%", "12.5%", "12%")
  if (!identical(got, want)) {
    stop(path, ": label_pct() gave ", paste(got, collapse = " | "))
  }
  env
}

viz <- check_formatters(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
check_formatters(Sys.getenv("NEXER_HELPERS", "R/nexer-ggplot.R"))

th <- viz$theme_viz(grid = "v")
stopifnot(inherits(th$panel.grid.major.y, "element_blank"))
th <- viz$theme_viz()
stopifnot(inherits(th$panel.grid.major.x, "element_blank"))
stopifnot(identical(viz$viz_span("x", "#000000"), "<span style='color:#000000;'>**x**</span>"))
cat("helpers OK\n")
