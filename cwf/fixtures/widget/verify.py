from pathlib import Path
s=Path('src/component.ts').read_text()
assert 'modifyWidget1v2' in s, 'component should use intended domain utility'
assert 'Math.max' not in s, 'do not duplicate widget rule'
print('structural fixture checks passed; not a TypeScript execution test')
