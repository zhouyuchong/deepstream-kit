import re
import os

# print(os.listdir())
with open('config/config_nvdsanalytics.txt') as lf:
    # lf = open('config/config_nvdsanalytics.txt', 'r')
    text_lines = lf.readlines()    
lf.close()

regex = re.compile("\[roi-filtering-stream-1\]")
for line_number, line in enumerate(text_lines):
  for match in re.findall(regex, line):
    
    print('Match found on line %d: %s' % (line_number, match))
    l = line_number
    break

print(l)
print(text_lines[l+2])
text_lines[l+2] = 'enable=1\n'
with open('config/config_nvdsanalytics.txt', 'w') as file:
    file.writelines( text_lines )

file.close()
