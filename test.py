test=[['a','b','c','d'],[0,2,0,5]]
test_dict={}

for i in test:
    print(i)
    test_dict[i[0]]=[i[1],i[2],i[3]]

print(test_dict)