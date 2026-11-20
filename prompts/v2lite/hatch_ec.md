
## Drawing hatch: "echarts" (ECharts, only when no key fits)

`"echarts"` is a partial ECharts option merged over the drawn chart, for drawing changes only (data changes go in
`data_code`). It is checked: styles, `title`, `legend`, `grid`, `xAxis`, `yAxis`, `series[i]` styles,
`markLine`/`markArea`/`markPoint`, and `graphic` text/line/rect are allowed; functions, links and data are not.
Series order: curves: y1 then y2 (combine: one y1 series per sheet, then y2); charts: one series per `by` value.

- Shade 300–450 °C: `"echarts": {"series": [{"markArea": {"data": [[{"xAxis": 300}, {"xAxis": 450}]], "itemStyle": {"color": "rgba(128,128,128,0.15)"}}}]}`
- Bold title: `"echarts": {"title": {"textStyle": {"fontWeight": "bold"}}}`
- Rotated x labels: `"echarts": {"xAxis": {"axisLabel": {"rotate": 30}}}`
An inset, a second x axis or a new panel cannot be done here: put it in `asks` as `unsupported`.
