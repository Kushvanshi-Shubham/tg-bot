#!/usr/bin/env python3
with open('src/bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 686: Change "INR amount you want to spend" to "USDT amount you want to buy"
for i, line in enumerate(lines):
    if 'Please type the INR amount you want to spend (e.g., 9000):' in line:
        lines[i] = line.replace(
            'Please type the INR amount you want to spend (e.g., 9000):',
            'Please type the USDT amount you want to buy (e.g., 100):'
        )
        print(f'Fixed line {i+1}')
    
    # Fix malformed emoji on line 685
    if '� You are paying with: INR' in line:
        lines[i] = line.replace('� You are paying with: INR', '💵 You are paying with: INR')
        # Add USDT receiving line after this
        lines.insert(i+1, '                f"🪙 You will receive: USDT\\n\\n"\n')
        print(f'Fixed emoji and added USDT line at {i+1}')
        break

with open('src/bot.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✅ Buyer workflow fixed!')
