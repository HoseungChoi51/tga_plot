
## Drawing hatch: "code" (matplotlib, only when no key fits)

`"code"` is Python run after drawing and before saving, for drawing changes only (data changes go in `data_code`).
Names: curves: `fig`, `ax1` (left y), `ax2` (right y or None), `plt`, `np`; charts: `fig`, `ax`, `plt`, `np`, `data`
(the drawn numbers). Changing `x` or `y1` here does nothing: the data is already drawn.

- Shade 300–450 °C: `"code": "ax1.axvspan(300, 450, color='gray', alpha=0.15)"`
- Arrow with text: `"code": "ax1.annotate('산화 시작', xy=(450, 90), xytext=(250, 60), arrowprops=dict(arrowstyle='->'))"`
- Hide the top frame: `"code": "ax.spines['top'].set_visible(False)"`
- Inset or a second x axis on top: draw it here with matplotlib.
