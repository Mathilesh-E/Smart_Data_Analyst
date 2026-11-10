
import re
import numpy as np
import pandas as pd

def read_data(file, name=None):
    name=(name or getattr(file,"name","data.csv")).lower()
    if hasattr(file, "seek"):
        try: file.seek(0)
        except Exception: pass
    if name.endswith(".csv"):
        try: df=pd.read_csv(file,low_memory=False,on_bad_lines="error")
        except UnicodeDecodeError:
            if hasattr(file, "seek"):
                try: file.seek(0)
                except Exception: pass
            df=pd.read_csv(file,encoding="latin-1",low_memory=False,on_bad_lines="error")
    elif name.endswith((".xlsx",".xls")): df=pd.read_excel(file)
    else: raise ValueError("Upload a CSV or Excel file.")
    if df.empty: raise ValueError("The file contains no data rows.")
    if len(df)>1_000_000: raise ValueError("Safety limit: 1,000,000 rows per upload.")
    cols=[]; seen={}
    for i,c in enumerate(df.columns):
        c=str(c).strip() or f"unnamed_{i+1}"
        seen[c]=seen.get(c,0)+1
        cols.append(c if seen[c]==1 else f"{c}_{seen[c]}")
    df.columns=cols
    return df

def kind(s):
    x=s.dropna()
    if x.empty: return "empty"
    n=re.sub(r"[\s\-]+","_",str(s.name).lower())
    if pd.api.types.is_bool_dtype(s): return "boolean"
    if pd.api.types.is_datetime64_any_dtype(s): return "datetime"
    if pd.api.types.is_numeric_dtype(s):
        if x.nunique()<=2: return "boolean"
        if len(x)>30 and x.nunique()/len(x)>.98 and re.search(r"(^|_)(id|key|code|number)($|_)",n): return "identifier"
        return "numeric"
    if s.dtype=="object" or pd.api.types.is_string_dtype(s):
        sample=x.astype(str).str.strip().head(300)
        sample_lower=sample.str.lower()
        bool_tokens={"true","false","yes","no","y","n","t","f","1","0"}
        if len(sample) and set(sample_lower.dropna().unique()) <= bool_tokens and sample_lower.nunique() <= 2:
            return "boolean"
        numeric=pd.to_numeric(sample,errors="coerce")
        if len(sample) and numeric.notna().all():
            if sample_lower.nunique()<=2: return "boolean"
            if len(x)>30 and x.nunique()/len(x)>.98 and re.search(r"(^|_)(id|key|code|number)($|_)",n): return "identifier"
            return "numeric"
        parsed=pd.to_datetime(sample,errors="coerce",format="mixed")
        if len(sample) and parsed.notna().mean()>=.85: return "datetime"
        if len(x)>30 and x.nunique()/len(x)>.98: return "identifier"
        return "categorical" if x.nunique()<=max(20,int(len(x)*.05)) else "text"
    return "categorical"

def profile(df):
    rows,cols=df.shape; missing=int(df.isna().sum().sum()); dup=int(df.duplicated().sum())
    kinds={c:kind(df[c]) for c in df}
    constant=[c for c in df if df[c].nunique(dropna=False)<=1]
    miss_pct=100*missing/max(rows*cols,1); dup_pct=100*dup/max(rows,1)
    score=max(0,min(100,100-.55*miss_pct-.25*dup_pct-.20*100*len(constant)/max(cols,1)))
    schema=[]
    for c in df:
        s=df[c]
        item={"Column":c,"Type":kinds[c],"Dtype":str(s.dtype),"Missing":int(s.isna().sum()),"Missing %":round(100*s.isna().mean(),2),"Unique":int(s.nunique()),"Unique %":round(100*s.nunique()/max(rows,1),2),"Sample":", ".join(s.dropna().astype(str).head(3))[:90],"Minimum":None,"Maximum":None,"Mean":None,"Median":None,"Std dev":None,"25th percentile":None,"75th percentile":None,"Most frequent":None}
        if kinds[c]=="numeric":
            x=pd.to_numeric(s,errors="coerce").replace([np.inf,-np.inf],np.nan).dropna()
            if len(x):
                item.update({"Minimum":float(x.min()),"Maximum":float(x.max()),"Mean":float(x.mean()),"Median":float(x.median()),"Std dev":float(x.std()) if len(x)>1 else 0.0,"25th percentile":float(x.quantile(.25)),"75th percentile":float(x.quantile(.75))})
        elif kinds[c]=="datetime":
            x=pd.to_datetime(s,errors="coerce").dropna()
            if len(x): item.update({"Minimum":x.min().isoformat(),"Maximum":x.max().isoformat()})
        if kinds[c] in ("categorical","boolean"):
            mode=s.mode(dropna=True)
            if len(mode): item["Most frequent"]=str(mode.iloc[0])
        schema.append(item)
    return {"rows":rows,"columns":cols,"missing":missing,"missing_pct":round(miss_pct,2),"duplicates":dup,"duplicate_pct":round(dup_pct,2),"quality":round(score,1),"kinds":kinds,"numeric":[c for c in df if kinds[c]=="numeric"],"categorical":[c for c in df if kinds[c] in ("categorical","boolean")],"dates":[c for c in df if kinds[c]=="datetime"],"constants":constant,"schema":schema}

def diagnostics(df,p):
    out=[]
    for c in df:
        s=df[c]; k=p["kinds"][c]; nout=0; infinite=0
        if k=="numeric":
            values=pd.to_numeric(s,errors="coerce")
            infinite=int(np.isinf(values).sum())
            x=values.replace([np.inf,-np.inf],np.nan).dropna()
            if len(x)>=4:
                q1,q3=x.quantile([.25,.75]); i=q3-q1
                nout=int(((x<q1-1.5*i)|(x>q3+1.5*i)).sum())
        out.append({"Column":c,"Type":k,"Missing":int(s.isna().sum()),"Missing %":round(100*s.isna().mean(),2),"Unique":int(s.nunique()),"IQR outlier candidates":nout,"Infinite values":infinite,"Constant":s.nunique(dropna=False)<=1})
    return pd.DataFrame(out)

def insights(df,p):
    a=[]
    if p["missing"]: a.append(("warning","Missing values",f"{p['missing']:,} cells ({p['missing_pct']}%) are missing. Review per-column patterns before choosing an imputation strategy."))
    else: a.append(("success","No missing cells","All cells are populated; values may still be invalid."))
    if p["duplicates"]: a.append(("warning","Duplicate records",f"{p['duplicates']:,} fully duplicated rows ({p['duplicate_pct']}%). Confirm whether repeats are legitimate."))
    if p["constants"]: a.append(("info","Constant columns","No variation detected in: "+", ".join(p["constants"][:8])+"."))
    for c in p["numeric"]:
        x=pd.to_numeric(df[c],errors="coerce").dropna()
        if len(x)>=10 and x.std()>0 and abs(x.skew())>1:
            a.append(("info",f"{c} is skewed",f"Skewness is {x.skew():.2f}; inspect its histogram and robust statistics."))
    for c in p["categorical"]:
        v=df[c].value_counts(dropna=True)
        if 2<=len(v)<=100 and v.iloc[0]/max(v.sum(),1)>=.8:
            a.append(("info",f"{c} is imbalanced",f"'{v.index[0]}' accounts for {v.iloc[0]/v.sum():.1%} of non-missing values."))
    if len(p["numeric"])>=2:
        corr=df[p["numeric"]].corr(); pairs=[]
        for i,x in enumerate(corr.columns):
            for y in corr.columns[i+1:]:
                if pd.notna(corr.loc[x,y]): pairs.append((abs(corr.loc[x,y]),x,y,corr.loc[x,y]))
        if pairs:
            _,x,y,v=max(pairs)
            if abs(v)>=.7: a.append(("info","Strong linear association",f"{x} and {y} have Pearson correlation {v:.2f}. Association is not causation."))
    return a[:12]

def recommendations(df,p):
    r=[]
    if p["duplicates"]: r.append({"key":"duplicates","label":f"Remove {p['duplicates']} fully duplicated rows","risk":"Review first"})
    for c in df:
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            has_padding=df[c].map(lambda value: isinstance(value,str) and value != value.strip()).any()
            if has_padding: r.append({"key":"whitespace:"+c,"label":f"Trim leading/trailing whitespace in {c}","risk":"Review first"})
        if df[c].isna().any():
            strategy="median" if p["kinds"][c]=="numeric" else ("mode" if p["kinds"][c] in ("categorical","boolean") else "leave")
            r.append({"key":"missing:"+c,"label":f"Fill missing values in {c} (suggested: {strategy})","strategy":strategy,"risk":"Review first"})
        if df[c].nunique(dropna=False)<=1: r.append({"key":"constant:"+c,"label":f"Drop constant column {c}","risk":"Confirm meaning"})
    return r

def clean(df, actions):
    out=df.copy(); log=[]
    for a in actions:
        k=a["key"]
        if k=="duplicates":
            n=len(out); out=out.drop_duplicates().copy(); log.append(f"Removed {n-len(out)} duplicate rows.")
        elif k.startswith("missing:"):
            c=k[8:]; method=a.get("strategy","leave")
            if c not in out: continue
            if method=="median" and pd.api.types.is_numeric_dtype(out[c]) and out[c].notna().any():
                n=int(out[c].isna().sum()); val=out[c].median(); out[c]=out[c].fillna(val); log.append(f"Filled {n} missing {c} values with median {val:g}.")
            elif method=="mode" and out[c].notna().any():
                n=int(out[c].isna().sum()); val=out[c].mode().iloc[0]; out[c]=out[c].fillna(val); log.append(f"Filled {n} missing {c} values with mode {val}.")
        elif k.startswith("constant:"):
            c=k[9:]
            if c in out and out[c].nunique(dropna=False)<=1: out=out.drop(columns=[c]); log.append(f"Dropped constant column {c}.")
        elif k.startswith("whitespace:"):
            c=k[11:]
            if c in out:
                mask=out[c].map(lambda value: isinstance(value,str) and value != value.strip())
                n=int(mask.sum())
                if n:
                    out.loc[mask,c]=out.loc[mask,c].map(str.strip)
                    log.append(f"Trimmed leading/trailing whitespace in {n} {c} values.")
    return out,log
