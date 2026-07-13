from fertility_popeve.variant.protein_parser import parse_hgvsp

print(parse_hgvsp("ENSP00000495403.1:p.Val78Ala"))
print(parse_hgvsp("ENSP00000340610.6:p.Ser12Phe"))
print(parse_hgvsp("ENSP00000331704.5:p.Pro232Leu"))
