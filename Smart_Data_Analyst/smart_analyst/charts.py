
import pandas as pd
import plotly.express as px
COLORS=["#8998FF","#37D6C0","#FFB86B","#FF7F9D","#B59CFF","#65B9FF"]
def make_chart(df,typ,x=None,y=None,color=None,bins=30,title=None):
    d=df.sample(50000,random_state=42) if len(df)>50000 else df
    if typ=="Histogram": f=px.histogram(d,x=x,color=color,nbins=bins,marginal="box",color_discrete_sequence=COLORS,title=title)
    elif typ=="Category count":
        q=d[x].astype("string").fillna("(Missing)").value_counts().head(25).rename_axis(x).reset_index(name="Count")
        f=px.bar(q,x=x,y="Count",color="Count",color_continuous_scale=["#26365E","#37D6C0"],title=title)
    elif typ=="Box plot": f=px.box(d,x=x,y=y,color=color,points="outliers",color_discrete_sequence=COLORS,title=title)
    elif typ=="Scatter": f=px.scatter(d,x=x,y=y,color=color,opacity=.75,color_discrete_sequence=COLORS,title=title)
    elif typ=="Line":
        q=d.groupby(x,dropna=False)[y].mean().reset_index().sort_values(x)
        f=px.line(q,x=x,y=y,markers=True,color_discrete_sequence=COLORS,title=title)
    elif typ=="Bar":
        q=d.groupby(x,dropna=False)[y].mean().reset_index().sort_values(y,ascending=False).head(30)
        f=px.bar(q,x=x,y=y,color=y,color_continuous_scale=["#26365E","#8998FF"],title=title)
    elif typ=="Correlation":
        n=d.select_dtypes(include="number")
        if n.shape[1]<2: raise ValueError("At least two numeric columns are required.")
        f=px.imshow(n.corr(),text_auto=".2f",zmin=-1,zmax=1,color_continuous_scale=["#F06B83","#111B31","#37D6C0"],title=title)
    else: raise ValueError("Unknown chart type")
    f.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#EAF0FF"),margin=dict(l=20,r=20,t=55,b=20),height=430)
    f.update_xaxes(showgrid=False); f.update_yaxes(gridcolor="rgba(150,170,220,.12)")
    return f
