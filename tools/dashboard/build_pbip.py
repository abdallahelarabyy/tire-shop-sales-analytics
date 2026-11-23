"""Generate the Tire Shop Power BI project (PBIP: TMDL semantic model + PBIR report).

Run:  python tools/dashboard/build_pbip.py   (narrative numbers come from tools/facts.py)
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dashboard"
NAME = "Tire Shop Sales Dashboard"
DATA_FOLDER = str(ROOT / "data" / "clean") + "\\"
import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from facts import compute, egp, pct  # noqa: E402
F = compute()
BASE_THEME_SRC = Path(__file__).parent / "Fluent2-CY26SU10.json"

VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

# Palette: colour-blind-safe; category colours match the EDA notebook
INK, INK2, MUTED, GRID, LINE = "#0B0B0B", "#52514E", "#8A8984", "#ECEBE7", "#E3E5E8"
HEADER, PAGE_BG = "#0F1E33", "#F3F4F6"
BLUE, ORANGE, AQUA, YELLOW, RED, GRAY = "#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#D03B3B", "#B9B8B3"


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "tireshop/" + "/".join(map(str, parts))))


def hexid(*parts):
    return hashlib.md5("/".join(map(str, parts)).encode()).hexdigest()[:20]


def q(name):
    """Quote a TMDL object name when needed."""
    return name if name.replace("_", "").isalnum() else "'" + name.replace("'", "''") + "'"


# =============================================================================
# Semantic model
# =============================================================================
# (model column, csv column, dataType, M type, formatString, hidden, sortBy, dateOnly)
def col(name, src, dtype="string", fmt=None, hidden=False, sort=None):
    mtype = {"string": "type text", "int64": "Int64.Type", "double": "type number",
             "boolean": "logical", "date": "type date", "dateTime": "type datetime"}[dtype]
    return dict(name=name, src=src, dtype=dtype, mtype=mtype, fmt=fmt, hidden=hidden, sort=sort)


TABLES = {
    "Products": dict(file="dim_product.csv", extra_m=[
        '#"Added Category Order" = Table.AddColumn(Kept, "category_order", each List.PositionOf({"Tire", "Battery", "Rim", "Service", "Accessory"}, [category]) + 1, Int64.Type)'],
        cols=[
            col("Product ID", "product_id", "int64", "0", hidden=True),
            col("Product", "product_name_en"),
            col("Product (Arabic)", "product_name_ar"),
            col("Category", "category", sort="Category Order"),
            col("Category Order", "category_order", "int64", "0", hidden=True),
            col("Brand", "brand"),
            col("Product Line", "product_line"),
            col("Origin Country", "origin_country"),
            col("Origin Region", "origin_region"),
            col("Tire Size", "tire_size"),
            col("Tire Type", "tire_type"),
            col("Rim Size", "rim_size_label", sort="Rim Diameter"),
            col("Rim Diameter", "rim_diameter_in", "int64", "0", hidden=True),
            col("Battery Model", "battery_model"),
            col("Battery Family", "battery_family"),
            col("Bolt Pattern", "rim_pcd"),
            col("Tags", "tags"),
            col("Possible Duplicate", "is_possible_duplicate", "boolean"),
        ]),
    "Product Sales": dict(file="fact_item_sales.csv", cols=[
        col("Product ID", "product_id", "int64", "0", hidden=True),
        col("Units", "qty_sold", "int64", "#,0", hidden=True),
        col("Sales Amount", "revenue", "double", "#,0", hidden=True),
        col("Cost Amount", "cost", "double", "#,0", hidden=True),
        col("Profit Amount", "profit", "double", "#,0", hidden=True),
        col("Unit Price", "unit_price", "double", "#,0"),
        col("Unit Cost", "unit_cost", "double", "#,0"),
        col("Product Margin", "margin_pct", "double", "0.0%"),
        col("ABC Class", "abc_class"),
        col("Profit Rank", "profit_rank", "int64", "0"),
        col("Price Band", "price_band", sort="Price Band Order"),
        col("Price Band Order", "price_band_order", "int64", "0", hidden=True),
        col("Margin Band", "margin_band", sort="Margin Band Order"),
        col("Margin Band Order", "margin_band_order", "int64", "0", hidden=True),
        col("Loss Gap", "loss_gap_band", sort="Loss Gap Order"),
        col("Loss Gap Order", "loss_gap_order", "int64", "0", hidden=True),
        col("Sale Status", "sale_status"),
    ]),
    "Invoices": dict(file="fact_invoices.csv", cols=[
        col("Invoice No", "invoice_no", "int64", "0"),
        col("Invoice DateTime", "invoice_datetime", "dateTime", "yyyy-mm-dd hh:nn"),
        col("Business Date", "business_date", "date", "yyyy-mm-dd"),
        col("Hour", "hour_label", sort="Hour Sort"),
        col("Hour Sort", "hour_sort", "int64", "0", hidden=True),
        col("Is After Midnight", "is_after_midnight", "boolean"),
        col("Date Corrected", "is_date_corrected", "boolean"),
        col("Days Shifted", "days_shifted", "int64", "0"),
        col("Time Estimated", "is_time_estimated", "boolean"),
        col("Customer Type", "customer_type"),
        col("Customer ID", "customer_id"),
        col("Items", "items_count", "int64", "0"),
        col("Gross Amount", "gross_amount", "double", "#,0", hidden=True),
        col("Discount", "discount", "double", "#,0", hidden=True),
        col("Tax", "tax", "double", "#,0", hidden=True),
        col("Net Amount", "net_amount", "double", "#,0", hidden=True),
        col("Paid Amount", "paid_amount", "double", "#,0", hidden=True),
        col("Due Amount", "due_amount", "double", "#,0", hidden=True),
        col("Payment Status", "payment_status"),
        col("Ticket Band", "ticket_band", sort="Ticket Band Order"),
        col("Ticket Band Order", "ticket_band_order", "int64", "0", hidden=True),
        col("Near Zero", "is_near_zero", "boolean"),
    ]),
    "Calendar": dict(file="dim_date.csv", date_table=True, cols=[
        col("Date", "date", "date", "yyyy-mm-dd"),
        col("Year", "year", "int64", "0"),
        col("Quarter", "quarter"),
        col("Month Num", "month_num", "int64", "0", hidden=True),
        col("Month", "month_name", sort="Month Num"),
        col("Month Short", "month_short", sort="Month Num"),
        col("Year Month", "year_month"),
        col("Month Start", "month_start", "date", "yyyy-mm-dd"),
        col("Day", "day_of_month", "int64", "0"),
        col("Weekday Num", "weekday_num", "int64", "0", hidden=True),
        col("Weekday", "weekday_name", sort="Weekday Num"),
        col("Weekday Short", "weekday_short", sort="Weekday Num"),
        col("Week Start", "week_start", "date", "yyyy-mm-dd"),
        col("Is Friday", "is_friday", "boolean"),
    ]),
}

SALES_STATUS = "'Product Sales'[Sale Status] = \"Sold below cost\""
HEAT_MAX = ("VAR mx = MAXX ( CROSSJOIN ( ALLSELECTED ( 'Calendar'[Weekday], 'Calendar'[Weekday Num] ), "
            "ALLSELECTED ( Invoices[Hour], Invoices[Hour Sort] ) ), [Invoice Count] )")
MEASURES = {
    "Product Sales": [
        ("Revenue", "SUM ( 'Product Sales'[Sales Amount] )", "#,0", "Sales"),
        ("Cost", "SUM ( 'Product Sales'[Cost Amount] )", "#,0", "Sales"),
        ("Profit", "SUM ( 'Product Sales'[Profit Amount] )", "#,0", "Sales"),
        ("Margin %", "DIVIDE ( [Profit], [Revenue] )", "0.0%", "Sales"),
        ("Units Sold", "SUM ( 'Product Sales'[Units] )", "#,0", "Sales"),
        ("Products Sold", "COUNTROWS ( 'Product Sales' )", "#,0", "Sales"),
        ("Avg Selling Price", "DIVIDE ( [Revenue], [Units Sold] )", "#,0", "Per unit"),
        ("Avg Cost per Unit", "DIVIDE ( [Cost], [Units Sold] )", "#,0", "Per unit"),
        ("Profit per Unit", "DIVIDE ( [Profit], [Units Sold] )", "#,0", "Per unit"),
        ("Revenue Share", "DIVIDE ( [Revenue], CALCULATE ( [Revenue], REMOVEFILTERS ( Products ) ) )", "0.0%", "Share"),
        ("Profit Share", "DIVIDE ( [Profit], CALCULATE ( [Profit], REMOVEFILTERS ( Products ) ) )", "0.0%", "Share"),
        ("Loss Products", f"COALESCE ( CALCULATE ( COUNTROWS ( 'Product Sales' ), {SALES_STATUS} ), 0 )", "#,0", "Pricing"),
        ("Loss Amount", f"- CALCULATE ( [Profit], {SALES_STATUS} )", "#,0", "Pricing"),
        ("Revenue at Loss", f"CALCULATE ( [Revenue], {SALES_STATUS} )", "#,0", "Pricing"),
        ("Low Margin Products", "COALESCE ( CALCULATE ( COUNTROWS ( 'Product Sales' ), 'Product Sales'[Margin Band] = \"0-5%\" ), 0 )", "#,0", "Pricing"),
        ("Category Color", f'SWITCH ( SELECTEDVALUE ( Products[Category] ), "Tire", "{BLUE}", "Battery", "{ORANGE}", '
                           f'"Rim", "{AQUA}", "Service", "{YELLOW}", "{MUTED}" )', None, "Formatting"),
        ("Margin Color", f'SWITCH ( TRUE (), ISBLANK ( [Margin %] ), "{INK2}", [Margin %] < 0, "{RED}", '
                         f'[Margin %] < 0.08, "#A35F00", "{INK}" )', None, "Formatting"),
    ],
    "Invoices": [
        ("Invoice Revenue", "SUM ( Invoices[Net Amount] )", "#,0", "Activity"),
        ("Invoice Count", "COUNTROWS ( Invoices )", "#,0", "Activity"),
        ("Avg Ticket", "DIVIDE ( [Invoice Revenue], [Invoice Count] )", "#,0", "Activity"),
        ("Trading Days", "DISTINCTCOUNT ( Invoices[Business Date] )", "#,0", "Activity"),
        ("Revenue per Trading Day", "DIVIDE ( [Invoice Revenue], [Trading Days] )", "#,0", "Activity"),
        ("Invoices per Day", "DIVIDE ( [Invoice Count], [Trading Days] )", "0.0", "Activity"),
        ("Revenue 7-Day Avg", [
            "VAR d = MAX ( 'Calendar'[Date] )",
            "VAR lastDay = CALCULATE ( MAX ( Invoices[Business Date] ), REMOVEFILTERS () )",
            "RETURN",
            "    IF ( d > lastDay, BLANK (), AVERAGEX ( DATESINPERIOD ( 'Calendar'[Date], d, -7, DAY ), [Invoice Revenue] ) )",
        ], "#,0", "Activity"),
        ("Share of Invoices", "DIVIDE ( [Invoice Count], CALCULATE ( [Invoice Count], REMOVEFILTERS ( Invoices[Ticket Band], Invoices[Ticket Band Order] ) ) )", "0%", "Activity"),
        ("Share of Revenue", "DIVIDE ( [Invoice Revenue], CALCULATE ( [Invoice Revenue], REMOVEFILTERS ( Invoices[Ticket Band], Invoices[Ticket Band Order] ) ) )", "0%", "Activity"),
        ("After-Midnight Revenue", "CALCULATE ( [Invoice Revenue], Invoices[Is After Midnight] = TRUE () )", "#,0", "Activity"),
        ("Evening Share", "DIVIDE ( CALCULATE ( [Invoice Count], Invoices[Hour Sort] >= 18 ), [Invoice Count] )", "0%", "Activity"),
        ("Heat Color", [
            "VAR v = [Invoice Count]",
            HEAT_MAX,
            "VAR r = DIVIDE ( v, mx )",
            "RETURN",
            '    SWITCH ( TRUE (), ISBLANK ( v ), "#FFFFFF", r < 0.2, "#EEF4FD", r < 0.4, "#B7D3F6", '
            'r < 0.6, "#6DA7EC", r < 0.8, "#2A78D6", "#184F95" )',
        ], None, "Formatting"),
        ("Heat Font Color", [
            "VAR v = [Invoice Count]",
            HEAT_MAX,
            'RETURN IF ( DIVIDE ( v, mx ) >= 0.6, "#FFFFFF", "#0B0B0B" )',
        ], None, "Formatting"),
    ],
}

RELATIONSHIPS = [
    ("Product Sales", "Product ID", "Products", "Product ID"),
    ("Invoices", "Business Date", "Calendar", "Date"),
]


def table_tmdl(tname, spec):
    L = [f"table {q(tname)}", f"\tlineageTag: {uid('table', tname)}"]
    if spec.get("date_table"):
        L.append("\tdataCategory: Time")
    L.append("")
    for name, expr, fmt, folder in MEASURES.get(tname, []):
        if isinstance(expr, list):
            L.append(f"\tmeasure {q(name)} =")
            L += [f"\t\t\t{line}" for line in expr]
        else:
            L.append(f"\tmeasure {q(name)} = {expr}")
        if fmt:
            L.append(f"\t\tformatString: {fmt}")
        L.append(f"\t\tdisplayFolder: {folder}")
        L.append(f"\t\tlineageTag: {uid('measure', tname, name)}")
        L.append("")
    for c in spec["cols"]:
        dtype = "dateTime" if c["dtype"] in ("date", "dateTime") else c["dtype"]
        L.append(f"\tcolumn {q(c['name'])}")
        L.append(f"\t\tdataType: {dtype}")
        if spec.get("date_table") and c["name"] == "Date":
            L.append("\t\tisKey")
        if c["hidden"]:
            L.append("\t\tisHidden")
        if c["fmt"]:
            L.append(f"\t\tformatString: {c['fmt']}")
        L.append(f"\t\tlineageTag: {uid('column', tname, c['name'])}")
        L.append("\t\tsummarizeBy: none")
        L.append(f"\t\tsourceColumn: {c['src']}")
        if c["sort"]:
            L.append(f"\t\tsortByColumn: {q(c['sort'])}")
        L.append("")
        L.append("\t\tannotation SummarizationSetBy = Automatic")
        if c["dtype"] == "date":
            L.append("")
            L.append("\t\tannotation UnderlyingDateTimeDataType = Date")
        L.append("")

    # Power Query partition
    loaded = [c for c in spec["cols"] if c["src"] != "category_order"]
    bools = [c["src"] for c in loaded if c["dtype"] == "boolean"]
    typed = [c for c in loaded if c["dtype"] != "boolean"]
    m = ["let", f'    Source = LoadCsv("{spec["file"]}"),']
    step = "Source"
    if bools:
        m.append("    #\"Booleans\" = Table.TransformColumns(Source, {"
                 + ", ".join(f'{{"{b}", each _ = "True", type logical}}' for b in bools) + "}),")
        step = '#"Booleans"'
    m.append(f"    #\"Changed Type\" = Table.TransformColumnTypes({step}, {{"
             + ", ".join(f'{{"{c["src"]}", {c["mtype"]}}}' for c in typed) + '}, "en-US"),')
    m.append("    Kept = Table.SelectColumns(#\"Changed Type\", {" + ", ".join(f'"{c["src"]}"' for c in loaded) + "})"
             + ("," if spec.get("extra_m") else ""))
    final = "Kept"
    for i, extra in enumerate(spec.get("extra_m", [])):
        m.append("    " + extra + ("," if i < len(spec["extra_m"]) - 1 else ""))
        final = extra.split(" = ")[0]
    m += ["in", f"    {final}"]
    L.append(f"\tpartition {q(tname)} = m")
    L.append("\t\tmode: import")
    L.append("\t\tsource =")
    L += [f"\t\t\t\t{line}" for line in m]
    L.append("")
    L.append("\tannotation PBI_ResultType = Table")
    L.append("")
    return "\n".join(L)


def write_model(sm: Path):
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (sm / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": uid("semanticmodel")}}, indent=2), encoding="utf-8")
    (sm / "definition.pbism").write_text(json.dumps({"version": "4.2", "settings": {}}, indent=2), encoding="utf-8")
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1606\n\n", encoding="utf-8")
    order = ["DataFolder", "LoadCsv"] + list(TABLES)
    (d / "model.tmdl").write_text("\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        f"annotation PBI_QueryOrder = {json.dumps(order)}", "",
        'annotation PBI_ProTooling = ["DevMode"]', ""] + [f"ref table {q(t)}" for t in TABLES] + ["", ""]),
        encoding="utf-8")
    (d / "expressions.tmdl").write_text("\n".join([
        f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
        f"\tlineageTag: {uid('expr', 'DataFolder')}", "", "\tannotation PBI_ResultType = Text", "",
        "expression LoadCsv =",
        "\t\t(fileName as text) as table =>",
        "\t\tlet",
        '\t\t    Source = Csv.Document(File.Contents(DataFolder & fileName), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        "\t\t    NoBom = Table.TransformColumnNames(Promoted, each Text.Replace(_, Character.FromNumber(65279), \"\")),",
        '\t\t    BlanksToNull = Table.TransformColumns(NoBom, {}, each if _ = "" then null else _)',
        "\t\tin",
        "\t\t    BlanksToNull",
        f"\tlineageTag: {uid('expr', 'LoadCsv')}", "", "\tannotation PBI_ResultType = Function", "", ""]),
        encoding="utf-8")
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {uid('rel', ft, fc)}", f"\tfromColumn: {q(ft)}.{q(fc)}", f"\ttoColumn: {q(tt)}.{q(tc)}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel) + "\n", encoding="utf-8")
    for t, spec in TABLES.items():
        (d / "tables" / f"{t}.tmdl").write_text(table_tmdl(t, spec), encoding="utf-8")


# =============================================================================
# Report helpers
# =============================================================================
def L(v): return {"expr": {"Literal": {"Value": v}}}
def S(s): return L("'" + str(s).replace("'", "''") + "'")
def B(b): return L("true" if b else "false")
def D(n): return L(f"{n}D")
def Cl(h): return {"solid": {"color": S(h)}}
def fld(kind, ent, prop): return {kind: {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}
def MCl(ent, prop): return {"solid": {"color": {"expr": fld("Measure", ent, prop)}}}


def proj(kind, ent, prop, name=None, active=False):
    p = {"field": fld(kind, ent, prop), "queryRef": f"{ent}.{prop}", "nativeQueryRef": name or prop}
    if name:
        p["displayName"] = name
    if active:
        p["active"] = True
    return p


def M(ent, prop, name=None): return proj("Measure", ent, prop, name)
def C(ent, prop, name=None, active=False): return proj("Column", ent, prop, name, active)
PS, INV, PRD, CAL = "Product Sales", "Invoices", "Products", "Calendar"


def query(roles, sort=None):
    qd = {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}
    if sort:
        kind, ent, prop, direction = sort
        qd["sortDefinition"] = {"sort": [{"field": fld(kind, ent, prop), "direction": direction}],
                                "isDefaultSort": False}
    return qd


def cat_filter(name, ent, prop, values, hidden=True):
    return {"name": name, "field": fld("Column", ent, prop), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "f", "Entity": ent, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}}],
                           "Values": [[{"Literal": {"Value": f"'{v}'"}}] for v in values]}}}]},
            "howCreated": "User", "isHiddenInViewMode": hidden}


def title(text):
    return [{"properties": {"show": B(True), "text": S(text), "fontSize": D(11), "bold": B(True),
                            "fontColor": Cl(INK)}}]


NO_CHROME = {"title": [{"properties": {"show": B(False)}}],
             "background": [{"properties": {"show": B(False)}}],
             "border": [{"properties": {"show": B(False)}}],
             "dropShadow": [{"properties": {"show": B(False)}}]}


class Page:
    def __init__(self, display, filters=None):
        self.display, self.name, self.visuals, self.z = display, hexid("page", display), [], 0
        self.filters = filters or []

    def add(self, vtype, x, y, w, h, query_=None, objects=None, vco=None, filters=None, key=None):
        self.z += 100
        v = {"$schema": VC_SCHEMA, "name": hexid(self.display, key or self.z),
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
             "visual": {"visualType": vtype}}
        if query_:
            v["visual"]["query"] = query_
        if objects:
            v["visual"]["objects"] = objects
        v["visual"]["visualContainerObjects"] = vco or {}
        v["visual"]["drillFilterOtherVisuals"] = True
        if filters:
            v["filterConfig"] = {"filters": filters}
        self.visuals.append(v)
        return v

    # ---- building blocks ------------------------------------------------------
    def header(self, subtitle):
        self.add("shape", 0, 0, 1280, 60, objects={
            "shape": [{"properties": {"tileShape": S("rectangle")}}],
            "fill": [{"properties": {"fillColor": Cl(HEADER), "transparency": D(0)}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": B(False)}}]}, vco=NO_CHROME, key="hdr")
        self.text(16, 6, 340, 50, [[("Tire Shop Analytics", dict(fontWeight="bold", fontSize="15pt", color="#FFFFFF"))],
                                    [(subtitle, dict(fontSize="9pt", color="#C9D1DC"))]], key="hdr_title")
        self.add("pageNavigator", 364, 13, 900, 34, objects={
            "layout": [{"properties": {"orientation": D(0), "rowCount": L("1L"), "columnCount": L("6L"),
                                       "cellPadding": L("6L")}}],   # 0 = grid
            "shape": [{"properties": {"tileShape": S("rectangleRounded"), "roundEdge": D(6)}}],
            "text": [{"properties": {"fontColor": Cl("#C9D1DC"), "fontSize": L("9.5D"), "leftMargin": D(6),
                                     "rightMargin": D(6), "horizontalAlignment": S("center")},
                      "selector": {"id": "default"}},
                     {"properties": {"fontColor": Cl("#FFFFFF"), "fontSize": L("9.5D")}, "selector": {"id": "hover"}},
                     {"properties": {"fontColor": Cl("#FFFFFF"), "fontSize": L("9.5D"), "bold": B(False)}, "selector": {"id": "selected"}}],
            "fill": [{"properties": {"show": B(True)}},
                     {"properties": {"fillColor": Cl(HEADER)}, "selector": {"id": "default"}},
                     {"properties": {"fillColor": Cl("#22344F")}, "selector": {"id": "hover"}},
                     {"properties": {"fillColor": Cl(BLUE)}, "selector": {"id": "selected"}}],
            "outline": [{"properties": {"show": B(False)}}]}, vco=NO_CHROME, key="nav")

    def text(self, x, y, w, h, paragraphs, key=None, boxed=False):
        paras = []
        for runs in paragraphs:
            paras.append({"textRuns": [{"value": t, "textStyle": st} for t, st in runs]})
        vco = dict(NO_CHROME)
        if boxed:
            vco = {"title": [{"properties": {"show": B(False)}}],
                   "padding": [{"properties": {k: D(12) for k in ("top", "bottom", "left", "right")}}]}
        return self.add("textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": paras}}]},
                        vco=vco, key=key)

    def card(self, x, y, w, h, ent, measure, label, units=1, precision=0, filters=None):
        return self.add("card", x, y, w, h, query({"Values": [M(ent, measure, label)]}), objects={
            "labels": [{"properties": {"color": Cl(INK), "fontSize": D(18), "labelDisplayUnits": D(units),
                                       "labelPrecision": L(f"{precision}L"), "fontFamily": S("Segoe UI Semibold")}}],
            "categoryLabels": [{"properties": {"show": B(True), "color": Cl(INK2), "fontSize": D(9)}}]},
            vco={"title": [{"properties": {"show": B(False)}}],
                 "padding": [{"properties": {k: D(2) for k in ("top", "bottom", "left", "right")}}]},
            filters=filters)

    def slicer(self, x, y, w, h, ent, column, label=None):
        return self.add("slicer", x, y, w, h, query({"Values": [C(ent, column, label, active=True)]}), objects={
            "data": [{"properties": {"mode": S("Dropdown")}}],
            "header": [{"properties": {"fontColor": Cl(INK2), "textSize": D(9)}}],
            "items": [{"properties": {"fontColor": Cl(INK), "textSize": D(10)}}]},
            vco={"title": [{"properties": {"show": B(False)}}]})

    def bars(self, vtype, x, y, w, h, title_, cat, values, sort, color=None, color_measure=None,
             filters=None, labels=True, series_colors=None, legend=False, axis=False):
        objects = {
            "valueAxis": [{"properties": {"show": B(axis), "showAxisTitle": B(False), "gridlineShow": B(axis),
                                          "gridlineColor": Cl(GRID)}}],
            "categoryAxis": [{"properties": {"showAxisTitle": B(False), "fontSize": D(9)}}],
            "labels": [{"properties": {"show": B(labels), "fontSize": D(9), "color": Cl(INK2)}}],
            "legend": [{"properties": {"show": B(legend), "position": S("Top"), "fontSize": D(9)}}],
            "general": [{"properties": {"responsive": B(False)}}],   # keep axis labels on short charts
        }
        if color_measure:
            objects["dataPoint"] = [{"properties": {"fill": MCl(*color_measure)},
                                     "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
        elif series_colors:
            objects["dataPoint"] = [{"properties": {"fill": Cl(c)}, "selector": {"metadata": ref}}
                                    for ref, c in series_colors]
        elif color:
            objects["dataPoint"] = [{"properties": {"fill": Cl(color)}}]
        return self.add(vtype, x, y, w, h, query({"Category": [cat], "Y": values}, sort), objects=objects,
                        vco={"title": title(title_)}, filters=filters)

    def table(self, x, y, w, h, title_, values, sort, filters=None, margin_ref=None, totals=True):
        objects = {
            "columnHeaders": [{"properties": {"backColor": Cl(HEADER), "fontColor": Cl("#FFFFFF"), "bold": B(True),
                                              "fontSize": D(9)}}],
            "values": [{"properties": {"fontSize": D(9), "fontColorPrimary": Cl(INK),
                                       "backColorSecondary": Cl("#F7F7F5")}}],
            "grid": [{"properties": {"gridHorizontal": B(True), "gridHorizontalColor": Cl(LINE)}}],
            "total": [{"properties": {"totals": B(totals), "bold": B(True)}}],
        }
        if margin_ref:
            objects["values"].append({"properties": {"fontColor": MCl(PS, "Margin Color")},
                                      "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                                   "metadata": margin_ref}})
        return self.add("tableEx", x, y, w, h, query({"Values": values}, sort), objects=objects,
                        vco={"title": title(title_)}, filters=filters)


def para(text, bold=False, size="10pt", color=INK):
    st = {"fontSize": size, "color": color}
    if bold:
        st["fontWeight"] = "bold"
    return [(text, st)]


def notes(*items, compact=False):
    """Heading/body pairs -> textbox paragraphs."""
    out = []
    for i, (head, body) in enumerate(items):
        if i and not compact:
            out.append(para(" ", size="5pt"))
        out.append(para(head, bold=True, size="9.5pt" if compact else "10.5pt", color=BLUE))
        out.append(para(body, size="9pt" if compact else "9.5pt"))
    return out


def cat_f(name, *cats):
    return [cat_filter(name, PRD, "Category", cats)]


MARGIN_REF = f"{PS}.Margin %"


# =============================================================================
# Pages
# =============================================================================
def build_pages():
    pages = []
    X = [16 + i * 210 for i in range(6)]

    # ---- 1. Overview ---------------------------------------------------------
    p = Page("Overview")
    p.header("Sales & profit (EGP, scaled for confidentiality)")
    cards = [(PS, "Revenue", "Revenue (EGP)", 1e6, 2), (PS, "Profit", "Profit (EGP)", 1e6, 2),
             (PS, "Margin %", "Margin", 1, 1), (PS, "Units Sold", "Units sold", 1, 0),
             (INV, "Invoice Count", "Invoices (1 Apr - 3 Nov)", 1, 0), (INV, "Avg Ticket", "Average ticket (EGP)", 1, 0)]
    for x, (ent, m, label, u, pr) in zip(X, cards):
        p.card(x, 72, 198, 86, ent, m, label, int(u), pr)
    cat = C(PRD, "Category", active=True)
    sort_cat = ("Column", PRD, "Category", "Ascending")
    for i, (m, t) in enumerate([("Revenue", "Revenue by category (EGP)"), ("Profit", "Profit by category (EGP)"),
                                ("Margin %", "Margin by category  (services: costs already deducted)")]):
        p.bars("clusteredBarChart", 16 + i * 420, 168, 408, 232, t, cat, [M(PS, m)], sort_cat,
               color_measure=(PS, "Category Color"), filters=cat_f(f"ov_cat{i}", "Tire", "Battery", "Rim", "Service"))
    p.bars("clusteredColumnChart", 16, 412, 612, 292, "Invoice revenue by month (EGP; Nov = 3 days only)",
           C(CAL, "Month Short", active=True), [M(INV, "Invoice Revenue")], ("Column", CAL, "Month Short", "Ascending"),
           color=BLUE)
    p.text(640, 412, 624, 292, notes(
        ("Services drive the profit", f"Welding and rim straightening are {pct(F['Service']['rev_share'])} of revenue but "
         f"{pct(F['Service']['profit_share'], 0)} of profit ({F['svc_jobs']:,} jobs)."),
        ("Goods earn thin margins", f"Tires {pct(F['Tire']['margin'])}, batteries {pct(F['Battery']['margin'])}, rims "
         f"{pct(F['Rim']['margin'])}. Bigger tires earn the least (R17 and up: {pct(F['big_margin'])})."),
        (f"{F['loss_n']} tires sold below cost", f"Against last purchase price; {F['gap']['Large (>15%)'][0]} of them more than "
         "15% below - see Pricing Alerts."),
        ("An evening business", f"{pct(F['evening_inv'], 0)} of invoices come after 18:00 (peak {F['peak_hour']}). "
         f"{F['best_month']} was the best month; Sep-Oct slowed."),
    ), boxed=True, key="insights")
    pages.append(p)

    # ---- 2. Tires ------------------------------------------------------------
    p = Page("Tires", filters=[cat_filter("tires_only", PRD, "Category", ["Tire"])])
    p.header("Tires: margin by size, price, origin, brand")
    for i, (column, label) in enumerate([("Rim Size", "Rim size"), ("Origin Country", "Origin"),
                                         ("Brand", "Brand"), ("Tire Type", "Tire type")]):
        p.slicer(16 + i * 156, 72, 148, 72, PRD, column, label)
    for i, (m, label, u, pr) in enumerate([("Revenue", "Tire revenue (EGP)", 1e6, 2), ("Profit", "Tire profit (EGP)", 1e3, 0),
                                           ("Margin %", "Tire margin", 1, 1), ("Units Sold", "Tires sold", 1, 0)]):
        p.card(648 + i * 156, 72, 148, 72, PS, m, label, int(u), pr)
    p.bars("clusteredColumnChart", 16, 152, 404, 252, "Margin by rim size", C(PRD, "Rim Size", active=True),
           [M(PS, "Margin %")], ("Column", PRD, "Rim Size", "Ascending"), color=BLUE)
    p.bars("clusteredColumnChart", 432, 152, 404, 252, "Margin by selling price per tire (EGP)",
           C(PS, "Price Band", active=True), [M(PS, "Margin %")], ("Column", PS, "Price Band", "Ascending"), color=BLUE)
    sc = p.add("scatterChart", 848, 152, 416, 252, query({
        "Category": [C(PRD, "Product", active=True)], "Series": [C(PS, "Sale Status")],
        "X": [M(PS, "Avg Selling Price", "Avg selling price")], "Y": [M(PS, "Margin %")],
        "Size": [M(PS, "Units Sold")]}), objects={
        "legend": [{"properties": {"show": B(True), "position": S("Top"), "fontSize": D(9)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": B(True), "gridlineShow": B(False)}}],
        "valueAxis": [{"properties": {"showAxisTitle": B(True), "gridlineColor": Cl(GRID)}}],
        "dataPoint": [{"properties": {"fill": Cl(BLUE)}, "selector": {"data": [{"scopeId": {"Comparison": {
                          "ComparisonKind": 0, "Left": fld("Column", PS, "Sale Status"),
                          "Right": {"Literal": {"Value": "'Profitable'"}}}}}]}},
                      {"properties": {"fill": Cl(RED)}, "selector": {"data": [{"scopeId": {"Comparison": {
                          "ComparisonKind": 0, "Left": fld("Column", PS, "Sale Status"),
                          "Right": {"Literal": {"Value": "'Sold below cost'"}}}}}]}}]},
        vco={"title": title("Every tire: price vs margin (size = units sold)")})
    p.table(16, 416, 404, 288, "By country of origin",
            [C(PRD, "Origin Country", "Origin"), M(PS, "Revenue"), M(PS, "Profit"), M(PS, "Margin %"), M(PS, "Units Sold", "Units")],
            ("Measure", PS, "Revenue", "Descending"), margin_ref=MARGIN_REF)
    p.table(432, 416, 404, 288, "By brand",
            [C(PRD, "Brand"), M(PS, "Revenue"), M(PS, "Profit"), M(PS, "Margin %"), M(PS, "Units Sold", "Units")],
            ("Measure", PS, "Profit", "Descending"), margin_ref=MARGIN_REF)
    p.table(848, 416, 416, 288, "Best-selling sizes",
            [C(PRD, "Tire Size", "Size"), M(PS, "Units Sold", "Units"), M(PS, "Products Sold", "Products"),
             M(PS, "Revenue"), M(PS, "Margin %")],
            ("Measure", PS, "Units Sold", "Descending"), margin_ref=MARGIN_REF)
    pages.append(p)

    # ---- 3. Batteries, rims & services ----------------------------------------
    p = Page("Batteries & Services")
    p.header("Batteries, rims and services")
    bat, rim, svc = cat_f("c_bat", "Battery"), cat_f("c_rim", "Rim"), cat_f("c_svc", "Service")
    for i, (m, label, u, pr) in enumerate([("Revenue", "Battery revenue (EGP)", 1e3, 0),
                                           ("Margin %", "Battery margin", 1, 1), ("Units Sold", "Batteries sold", 1, 0)]):
        p.card(16 + i * 208, 72, 200, 72, PS, m, label, int(u), pr, filters=cat_f(f"bc{i}", "Battery"))
    for i, (m, label, u, pr, f) in enumerate([("Profit", "Service profit (EGP)", 1e3, 0, "Service"),
                                              ("Units Sold", "Service jobs", 1, 0, "Service"),
                                              ("Profit per Unit", "Profit per job (EGP)", 1, 0, "Service"),
                                              ("Revenue", "Rim revenue (EGP)", 1e3, 0, "Rim")]):
        p.card(648 + i * 156, 72, 148, 72, PS, m, label, int(u), pr, filters=cat_f(f"sc{i}", f))
    p.bars("clusteredBarChart", 16, 156, 304, 260, "Battery revenue by line (EGP)", C(PRD, "Product Line", active=True),
           [M(PS, "Revenue")], ("Measure", PS, "Revenue", "Descending"), color=ORANGE, filters=bat)
    p.bars("clusteredBarChart", 328, 156, 304, 260, "Battery margin by line", C(PRD, "Product Line", active=True),
           [M(PS, "Margin %")], ("Measure", PS, "Margin %", "Descending"), color=ORANGE, filters=cat_f("c_bat2", "Battery"))
    p.table(648, 156, 616, 150, "Services (costs are small and already deducted from revenue)",
            [C(PRD, "Product", "Service"), M(PS, "Units Sold", "Jobs"), M(PS, "Revenue"), M(PS, "Profit"),
             M(PS, "Avg Selling Price", "Avg price per job")], ("Measure", PS, "Revenue", "Descending"), filters=svc,
            totals=False)
    p.text(648, 316, 616, 100, notes(
        ("Services are the most valuable line", f"{pct(F['Service']['profit_share'], 0)} of all profit and most of the walk-in traffic."),
        ("Egyptian batteries earn about twice the margin",
         f"Chloride {pct(F['bat_lines']['Chloride Gold']['margin'], 0)}-{pct(F['bat_lines']['Chloride Standard']['margin'], 0)}, "
         f"Nesr {pct(F['bat_lines']['Nesr']['margin'], 0)} vs Varta {pct(F['bat_lines']['Varta']['margin'])}, ACDelco "
         f"{pct(F['bat_lines']['ACDelco']['margin'])}. TD-70 = {F['td70_share']:.0%} of units."),
        compact=True), boxed=True, key="bat_notes")
    p.bars("clusteredColumnChart", 16, 428, 616, 276, "Batteries sold by model", C(PRD, "Battery Model", active=True),
           [M(PS, "Units Sold")], ("Measure", PS, "Units Sold", "Descending"), color=ORANGE, filters=cat_f("c_bat3", "Battery"))
    p.table(648, 428, 616, 276, "Rims (each sold once)",
            [C(PRD, "Product", "Rim"), C(PRD, "Bolt Pattern"), M(PS, "Revenue"), M(PS, "Profit"), M(PS, "Margin %")],
            ("Measure", PS, "Revenue", "Descending"), filters=rim, margin_ref=MARGIN_REF)
    pages.append(p)

    # ---- 4. Pricing alerts -----------------------------------------------------
    p = Page("Pricing Alerts")
    p.header("Pricing alerts (cost = last purchase price)")
    p.slicer(16, 72, 160, 72, PRD, "Category")
    p.slicer(184, 72, 168, 72, PS, "Loss Gap", "How far below cost")
    for i, (m, label) in enumerate([("Loss Products", "Products sold below cost"), ("Loss Amount", "Lost vs last purchase price (EGP)"),
                                    ("Revenue at Loss", "Revenue on those products (EGP)"),
                                    ("Low Margin Products", "Products at 0-5% margin")]):
        p.card(364 + i * 226, 72, 218, 72, PS, m, label, 1, 0)
    p.bars("clusteredBarChart", 16, 156, 400, 270, "Loss by product (EGP below last purchase price)",
           C(PRD, "Product", active=True), [M(PS, "Loss Amount")], ("Measure", PS, "Loss Amount", "Descending"), color=RED)
    p.bars("clusteredColumnChart", 428, 156, 412, 270, "Revenue by margin band (EGP)", C(PS, "Margin Band", active=True),
           [M(PS, "Revenue")], ("Column", PS, "Margin Band", "Ascending"), color=BLUE)
    p.bars("clusteredColumnChart", 852, 156, 412, 270, "Products by margin band", C(PS, "Margin Band", active=True),
           [M(PS, "Products Sold")], ("Column", PS, "Margin Band", "Ascending"), color=BLUE)
    p.table(16, 438, 1248, 266, "Products sold below their last purchase price - check large gaps against purchase history",
            [C(PRD, "Product"), C(PS, "Loss Gap", "Gap below cost"), M(PS, "Units Sold", "Units"),
             M(PS, "Avg Selling Price", "Avg selling price"), M(PS, "Avg Cost per Unit", "Last purchase price"),
             M(PS, "Profit"), M(PS, "Margin %")],
            ("Measure", PS, "Profit", "Ascending"), filters=[cat_filter("loss_only", PS, "Sale Status", ["Sold below cost"])],
            margin_ref=MARGIN_REF)
    pages.append(p)

    # ---- 5. Sales activity -----------------------------------------------------
    p = Page("Sales Activity")
    p.header("Sales activity: invoices 1 Apr - 3 Nov 2026")
    p.slicer(16, 72, 150, 72, CAL, "Month Short", "Month")
    p.slicer(174, 72, 150, 72, CAL, "Weekday")
    for i, (m, label, u, pr) in enumerate([("Invoice Revenue", "Revenue (EGP)", 1e6, 2), ("Invoice Count", "Invoices", 1, 0),
                                           ("Trading Days", "Trading days", 1, 0),
                                           ("Revenue per Trading Day", "Revenue per trading day", 1e3, 1),
                                           ("Avg Ticket", "Average ticket (EGP)", 1, 0)]):
        p.card(332 + i * 188, 72, 180, 72, INV, m, label, int(u), pr)
    p.add("lineChart", 16, 152, 820, 210, query({
        "Category": [C(CAL, "Date", active=True)],
        "Y": [M(INV, "Invoice Revenue", "Daily revenue"), M(INV, "Revenue 7-Day Avg", "7-day average")]}), objects={
        "dataPoint": [{"properties": {"fill": Cl(GRAY)}, "selector": {"metadata": f"{INV}.Invoice Revenue"}},
                      {"properties": {"fill": Cl(BLUE)}, "selector": {"metadata": f"{INV}.Revenue 7-Day Avg"}}],
        "lineStyles": [{"properties": {"strokeWidth": D(1)}, "selector": {"metadata": f"{INV}.Invoice Revenue"}},
                       {"properties": {"strokeWidth": D(3)}, "selector": {"metadata": f"{INV}.Revenue 7-Day Avg"}}],
        "legend": [{"properties": {"show": B(True), "position": S("Top"), "fontSize": D(9)}}],
        "general": [{"properties": {"responsive": B(False)}}],
        "valueAxis": [{"properties": {"showAxisTitle": B(False), "gridlineColor": Cl(GRID)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": B(False)}}]},
        vco={"title": title("Daily revenue (EGP) - closed 26 May - 2 Jun for Eid al-Adha")})
    p.add("pivotTable", 16, 374, 744, 330, query({
        "Rows": [C(CAL, "Weekday", active=True)], "Columns": [C(INV, "Hour")], "Values": [M(INV, "Invoice Count", "Invoices")]}),
        objects={
            "values": [{"properties": {"fontSize": D(8)}},
                       {"properties": {"backColor": MCl(INV, "Heat Color"), "fontColor": MCl(INV, "Heat Font Color")},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{INV}.Invoice Count"}}],
            "columnHeaders": [{"properties": {"fontSize": D(8), "backColor": Cl("#FFFFFF"), "fontColor": Cl(INK2)}}],
            "rowHeaders": [{"properties": {"fontSize": D(9), "fontColor": Cl(INK2)}}],
            "subTotals": [{"properties": {"rowSubtotals": B(False), "columnSubtotals": B(False)}}],
            "grid": [{"properties": {"gridVertical": B(True), "gridVerticalColor": Cl("#FFFFFF"),
                                     "gridHorizontal": B(True), "gridHorizontalColor": Cl("#FFFFFF")}}]},
        vco={"title": title("Invoices by weekday and hour (darker = busier)")})
    p.bars("clusteredColumnChart", 848, 152, 416, 210, "Revenue per trading day by weekday (EGP)",
           C(CAL, "Weekday Short", active=True), [M(INV, "Revenue per Trading Day")],
           ("Column", CAL, "Weekday Short", "Ascending"), color=BLUE)
    p.bars("clusteredColumnChart", 772, 374, 492, 330, "Share of invoices vs share of revenue, by invoice value (EGP)",
           C(INV, "Ticket Band", active=True), [M(INV, "Share of Invoices"), M(INV, "Share of Revenue")],
           ("Column", INV, "Ticket Band", "Ascending"),
           series_colors=[(f"{INV}.Share of Invoices", GRAY), (f"{INV}.Share of Revenue", BLUE)], legend=True)
    pages.append(p)

    # ---- 6. Data notes ---------------------------------------------------------
    p = Page("Data Notes")
    p.header("About the data")
    p.text(16, 72, 616, 632, notes(
        ("Real data, kept confidential", "Real point-of-sale data from a family-owned tire, battery and rim shop in "
         "Egypt. The shop is not named, customer names are removed, and all money values are scaled by a secret "
         "factor and perturbed per product. Percentages, counts, dates and patterns are real; EGP amounts are not."),
        ("Sources", f"Two exports from the shop's DEXEF POS: the item profit report ({F['products']} products: quantity, "
         f"revenue, cost, profit) and the invoice list ({F['inv_n']:,} invoices, 1 Apr - 3 Nov 2026). The item report "
         "has no dates or invoice numbers, so product pages and activity pages cannot be cross-filtered."),
        ("Cost basis", "DEXEF values cost at the LAST PURCHASE PRICE (replacement cost). When supplier prices rise, "
         "older stock is valued at the new price, so margins look lower than what was actually earned and some sales "
         "show as losses. The owner confirmed some tires were knowingly sold below cost."),
        ("Services", "Welding and rim straightening have no cost in the POS. Their costs are small and already "
         "deducted from the service revenue, so the recorded service profit is used as-is."),
        ("Cleaning (Python)", "Product names parsed into category, size, brand and origin (Arabic -> English). "
         f"3 duplicate invoice rows removed; {F['corrected']} invoice dates corrected (the POS kept the open shift's date); sales "
         "before 05:00 count for the previous trading day; customer names replaced by IDs. "
         "All totals reconcile with the POS report footers."),
    ), boxed=True, key="notes1")
    p.text(648, 72, 616, 632, notes(
        ("Definitions", "Revenue, Cost, Profit: item report totals. Margin = Profit / Revenue. "
         "Invoice revenue: net invoice value (after discounts). Trading day: a business date with at "
         "least one invoice. Average ticket = invoice revenue / invoices."),
        ("Bands", "Price band: average selling price per tire. Margin band: product margin. Gap below cost: how far "
         "below the last purchase price a loss product sold (small < 5%, medium 5-15%, large > 15%)."),
        ("Known gaps", f"Item revenue ({egp(F['revenue'])}) is higher than invoice revenue ({egp(F['inv_rev'])}) because "
         "the invoice export ends 3 Nov while the item report runs to 22 Nov. "
         f"{pct(F['walkin_share'], 0)} of invoices are walk-in cash, so there is no customer history."),
        ("Reproduce", "run_pipeline.bat rebuilds the clean data and the notebook from data/raw. If the project "
         "folder moves, update the DataFolder parameter (Transform data > Edit parameters) and click Refresh."),
    ), boxed=True, key="notes2")
    pages.append(p)
    return pages


# =============================================================================
# Theme & report files
# =============================================================================
THEME = {
    "name": "Tire Shop",
    "dataColors": [BLUE, RED, AQUA, YELLOW, "#E87BA4", "#008300", "#6250D6", ORANGE],
    "foreground": INK, "foregroundNeutralSecondary": INK2, "foregroundNeutralTertiary": MUTED,
    "background": "#FFFFFF", "backgroundLight": "#F7F7F5", "backgroundNeutral": LINE,
    "tableAccent": BLUE, "good": "#0CA30C", "neutral": "#FAB219", "bad": RED,
    "maximum": "#184F95", "center": "#6DA7EC", "minimum": "#EEF4FD",
    "textClasses": {
        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 20, "color": INK},
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": INK},
        "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": INK},
        "label": {"fontFace": "Segoe UI", "fontSize": 9, "color": INK2}},
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
            "border": [{"show": True, "color": {"solid": {"color": LINE}}, "radius": 8}],
            "dropShadow": [{"show": False}],
            "title": [{"show": True, "fontColor": {"solid": {"color": INK}}, "fontSize": 11, "bold": True}],
            "subTitle": [{"show": False}],
            "visualHeader": [{"show": True}]}},
        "page": {"*": {
            "background": [{"color": {"solid": {"color": PAGE_BG}}, "transparency": 0}],
            "outspace": [{"color": {"solid": {"color": PAGE_BG}}}]}}},
}


def write_report(rp: Path, pages):
    d = rp / "definition"
    (d / "pages").mkdir(parents=True, exist_ok=True)
    (rp / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": uid("report")}}, indent=2), encoding="utf-8")
    (rp / "definition.pbir").write_text(json.dumps({
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2), encoding="utf-8")
    (d / "version.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"}, indent=2), encoding="utf-8")
    at_import = {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"}
    (d / "report.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "Fluent2-CY26SU10", "reportVersionAtImport": at_import, "type": "SharedResources"},
            "customTheme": {"name": "TireShop_Theme.json", "reportVersionAtImport": at_import, "type": "RegisteredResources"}},
        "objects": {"outspacePane": [{"properties": {"expanded": B(False)}}]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "Fluent2-CY26SU10", "path": "BaseThemes/Fluent2-CY26SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "TireShop_Theme.json", "path": "TireShop_Theme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}}, indent=2), encoding="utf-8")
    base = rp / "StaticResources" / "SharedResources" / "BaseThemes"
    base.mkdir(parents=True, exist_ok=True)
    shutil.copy(BASE_THEME_SRC, base / BASE_THEME_SRC.name)
    reg = rp / "StaticResources" / "RegisteredResources"
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "TireShop_Theme.json").write_text(json.dumps(THEME, indent=2), encoding="utf-8")

    (d / "pages" / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name}, indent=2), encoding="utf-8")
    for p in pages:
        pd_ = d / "pages" / p.name
        (pd_ / "visuals").mkdir(parents=True, exist_ok=True)
        page = {"$schema": PAGE_SCHEMA, "name": p.name, "displayName": p.display, "displayOption": "FitToPage",
                "height": 720, "width": 1280}
        if p.filters:
            page["filterConfig"] = {"filters": p.filters}
        (pd_ / "page.json").write_text(json.dumps(page, indent=2), encoding="utf-8")
        for v in p.visuals:
            vd = pd_ / "visuals" / v["name"]
            vd.mkdir(parents=True, exist_ok=True)
            (vd / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")


def main():
    # Replace only the generated definitions; keep Power BI's .pbi folders (local settings + data cache)
    for child in [OUT / f"{NAME}.Report" / "definition", OUT / f"{NAME}.SemanticModel" / "definition"]:
        if child.exists():
            shutil.rmtree(child)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{NAME}.pbip").write_text(json.dumps({
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2), encoding="utf-8")
    (OUT / ".gitignore").write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n", encoding="utf-8")
    write_model(OUT / f"{NAME}.SemanticModel")
    pages = build_pages()
    write_report(OUT / f"{NAME}.Report", pages)
    n = sum(len(p.visuals) for p in pages)
    print(f"written {OUT} - {len(pages)} pages, {n} visuals")


if __name__ == "__main__":
    main()
