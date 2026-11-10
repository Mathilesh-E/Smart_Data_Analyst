import pandas as pd
from smart_analyst import kind, profile, insights, recommendations, clean


def test_profile_and_missing():
 d=pd.DataFrame({"age":[20,30,None,40],"city":["A","B","A",None]}); p=profile(d)
 assert p["rows"]==4 and p["missing"]==2 and 0<=p["quality"]<=100
 age=next(column for column in p["schema"] if column["Column"]=="age")
 assert age["Minimum"]==20 and age["Median"]==30 and age["Mean"]==30

def test_inference():
 assert kind(pd.Series([1,2,3],name="age"))=="numeric"
 assert kind(pd.Series(["x","y","x"],name="city"))=="categorical"
 assert kind(pd.Series([True,False,None],name="active"))=="boolean"
 assert kind(pd.Series(["1","2","3",None],name="score"))=="numeric"

def test_numeric_identifier_names_with_spaces_are_not_measures():
 assert kind(pd.Series(range(50),name="Row ID"))=="identifier"
 assert kind(pd.Series(range(50),name="Postal Code"))=="identifier"
 assert kind(pd.Series(range(50),name="revenue"))=="numeric"

def test_clean_copy():
 d=pd.DataFrame({"age":[1,None,3]}); a={"key":"missing:age","strategy":"median"}; out,log=clean(d,[a])
 assert d.age.isna().sum()==1 and out.age.isna().sum()==0 and log

def test_trim_whitespace_cleaning_is_opt_in():
 d=pd.DataFrame({"city":[" West ","East",None]}); p=profile(d)
 action=next(item for item in recommendations(d,p) if item["key"]=="whitespace:city")
 out,log=clean(d,[action])
 assert d.loc[0,"city"]==" West " and out.loc[0,"city"]=="West" and log

def test_insights():
 d=pd.DataFrame({"x":[1,2,None,4]}); p=profile(d); assert insights(d,p)
