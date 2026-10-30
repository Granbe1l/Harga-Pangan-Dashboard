#!/usr/bin/env python3
"""Inspect and stage primary data. Never silently overwrite the active mirror snapshot."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyst.primary import inspect_landing,stage_download,stage_normalized


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    inspect=commands.add_parser("inspect");inspect.add_argument("--output",type=Path,required=True)
    fetch=commands.add_parser("download");fetch.add_argument("--url",required=True);fetch.add_argument("--output",type=Path,required=True)
    normalize=commands.add_parser("normalize")
    normalize.add_argument("--input",type=Path,required=True);normalize.add_argument("--mapping",type=Path,required=True)
    normalize.add_argument("--output",type=Path,required=True);normalize.add_argument("--date-format",default="%Y-%m-%d")
    normalize.add_argument("--delimiter",default=",");normalize.add_argument("--decimal",default=".");normalize.add_argument("--thousands",default=None)
    args=parser.parse_args()
    if args.command=="inspect":result=inspect_landing(args.output)
    elif args.command=="download":result={"saved":str(stage_download(args.url,args.output))}
    else:result=stage_normalized(args.input,args.mapping,args.output,date_format=args.date_format,delimiter=args.delimiter,decimal=args.decimal,thousands=args.thousands)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
