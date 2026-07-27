#!/usr/bin/env python3

from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/phenotype/raw")
OUT_DIR = Path("data/phenotype")


MAIN_FILE = RAW_DIR / "样本收集信息汇总-表型分型20260427.xlsx"
SUB_FILE = RAW_DIR / "样本收集信息汇总-亚表型分类20260608.xlsx"


def binary(x):
    if pd.isna(x):
        return 0

    x = str(x).strip()

    if x in ["", "NO", "/", "nan"]:
        return 0

    return 1


def get_col(row, names):

    for n in names:
        if n in row.index:
            return row[n]

    return ""



def clean_value(x):
    if pd.isna(x):
        return None

    x = str(x).strip()

    if x in ["/", "", "nan", "None"]:
        return None

    return x

def main():

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    # ======================
    # main phenotype
    # ======================

    records = []
    metadata = []


    for cohort, sheet in [
        ("OMD", "OMD组"),
        ("PT", "PT组")
    ]:

        df = pd.read_excel(
            MAIN_FILE,
            sheet_name=sheet
        )


        for _, row in df.iterrows():

            sid = row["SampleID"]


            phenotype_text = str(
                get_col(
                    row,
                    [
                        "表型（omd卵子缺陷，nf受精障碍,ed胚胎停育）",
                        "表型(ed胚胎缺陷，ap非整倍体,ud未知表型)"
                    ]
                )
            ).lower()


            records.append(
                {

                    "sample_id": sid,
                    "cohort": cohort,

                    "OMD":
                        1 if cohort=="OMD" else 0,

                    "NF":
                        binary(
                            get_col(
                                row,
                                [
                                    "受精障碍（NF不受精，PS多精受精）",
                                    "受精障碍（NF，PS）"
                                ]
                            )
                        ),

                    "EA":
                        binary(
                            row["胚胎停育（EA）"]
                        ),

                    "ED":
                        1 if "ed" in phenotype_text else 0,

                    "AP":
                        1 if "ap" in phenotype_text else 0,

                    "UD":
                        1 if "ud" in phenotype_text else 0,


                    "positive_gene":
                        str(row["Positive"])
                }
            )


            metadata.append(
                {
                    "sample_id": sid,
                    "cohort": cohort,
                    "age": clean_value(row["Age"]),
                    "primary_infertility": clean_value(row["原发未孕"]),
                    "ivf_cycles": clean_value(row["IVF/ICSI cycles"]),
                }
            )


    phenotype = pd.DataFrame(records)


    # merge duplicate samples

    phenotype = (
        phenotype
        .groupby(
            "sample_id",
            as_index=False
        )
        .agg(
            {
                "cohort":"first",

                "OMD":"max",
                "NF":"max",
                "EA":"max",
                "ED":"max",
                "AP":"max",
                "UD":"max",

                "positive_gene":
                    lambda x:
                    ";".join(
                        sorted(
                            set(
                                str(i)
                                for i in x
                                if str(i)!="NO"
                            )
                        )
                    )
                    if any(
                        str(i)!="NO"
                        for i in x
                    )
                    else "NO"
            }
        )
    )


    phenotype.to_csv(
        OUT_DIR/"phenotype.csv",
        index=False
    )


    metadata = pd.DataFrame(metadata)

    metadata = (
        metadata
        .drop_duplicates(
            "sample_id"
        )
    )


    metadata.to_csv(
        OUT_DIR/"sample_metadata.csv",
        index=False
    )


    # ======================
    # sub phenotype
    # ======================

    mapping = {

        "异常卵AD":"AD",
        "空卵EF":"EF",
        "蜡状ZP":"ZP",

        "GV阻滞":"GV",
        "MI阻滞":"MI",

        "NF不受精":"NF",
        "PS多原核":"PS",

        "AP非整倍体":"AP",
        "ED胚胎停育":"ED"
    }


    sub_records=[]


    xls = pd.ExcelFile(
        SUB_FILE
    )


    for sheet,label in mapping.items():

        if sheet not in xls.sheet_names:
            continue


        df = pd.read_excel(
            SUB_FILE,
            sheet_name=sheet
        )


        for _,row in df.iterrows():

            sid=row["SampleID"]

            sub_records.append(
                {
                    "sample_id":sid,
                    "subphenotype":label,
                    "source_sheet":sheet,
                    "positive_gene":
                        str(row["Positive"])
                        if "Positive" in row.index
                        else "NO"
                }
            )


    sub = pd.DataFrame(sub_records)


    sub.drop_duplicates(
        inplace=True
    )


    sub.to_csv(
        OUT_DIR/"subphenotype.csv",
        index=False
    )


    print("phenotype:", phenotype.shape)
    print("metadata:", metadata.shape)
    print("subphenotype:", sub.shape)


if __name__=="__main__":
    main()
