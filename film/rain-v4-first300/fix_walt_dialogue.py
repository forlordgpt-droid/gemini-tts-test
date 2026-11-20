from pathlib import Path
p=Path("film/rain-v4-first300/scenes/main.js")
s=p.read_text(encoding="utf-8")
old="if(id===62||id===63){pill(id===62?'“YOU’RE BUYING SOUP.”':'“I’M BUYING A BUILDING.”',145,730,a,true);}"
new="if(id===62||id===63){const opacity=smooth(u/.24)*smooth((d-u)/.22);pill(id===62?'“YOU’RE BUYING SOUP.”':'“I’M BUYING A BUILDING.”',145,730,opacity,true);}"
assert s.count(old)==1, "Source changed; stop instead of patching unexpectedly"
p.write_text(s.replace(old,new),encoding="utf-8")
print("Walt dialogue opacity fixed without changing imagery, narration, or other scenes")
