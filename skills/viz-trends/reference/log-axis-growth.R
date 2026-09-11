# A log axis for growth: a constant growth rate is a straight line, and the
# axis is labelled in the real values, not in logs.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

# Personal consumption expenditure, monthly, in dollars (the source is in
# billions). Fifty years of roughly exponential growth.
spend <- ggplot2::economics |>
  mutate(pce = pce * 1e9)

# The average yearly growth rate is the slope of a straight line on the log
# scale. It goes into the title and the Note, computed rather than typed.
years <- as.numeric(spend$date - min(spend$date)) / 365.25
fit <- lm(log(spend$pce) ~ years)
rate <- label_pct(accuracy = 0.1)(exp(coef(fit)[[2]]) - 1)

p <- ggplot(spend, aes(date, pce)) +
  geom_line(colour = viz_colours[["single"]], linewidth = 1) +
  geom_smooth(method = "lm", formula = y ~ x, se = FALSE,
              colour = viz_colours[["highlight"]], linetype = "dashed", linewidth = 0.7) +
  scale_y_log10(labels = label_short(), breaks = c(5e11, 1e12, 2e12, 5e12, 1e13)) +
  scale_x_date(date_breaks = "10 years", date_labels = "%Y") +
  labs(
    title = paste("US consumer spending has grown", rate, "a year for five decades"),
    subtitle = "Personal consumption expenditure, monthly, log scale",
    x = NULL, y = "Spending (USD per year, log scale)",
    caption = paste0("Note: dashed line is a linear fit on the log scale; ", rate,
                     " is its slope. Source: ggplot2::economics (US FRED)")
  ) +
  theme_viz()

path <- file.path(out_dir, "log-axis-growth.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
