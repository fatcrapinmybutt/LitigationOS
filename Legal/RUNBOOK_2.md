# Plugin runner (FIX11)
Build stamp (local): 2026-01-20 07:31:40

## What it does
Runs staged operations with checkpoint JSONs (SavePoints) under:
- `sp/plg/<stage>/checkpoint.json`

## Run all stages (in registry order)
`python plg\runner.py --root F:\L3`

## Resume (skip completed)
`python plg\runner.py --root F:\L3 --resume`

## Run selected stages
`python plg\runner.py --root F:\L3 --stages c3,val,docs`

## Stage registry
- `plg\_registry.json`
