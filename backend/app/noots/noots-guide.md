
# Noots Noots Noots

to create a reference guide for models and their relationships before the refactor: from noots directory, run this:

grep -n "Archetype" ../models.py >> model-noots/AM.txt && grep -n "Archetype" ../crud.py >> crud-noots/arch-crud-noots.txt && grep -n "Quality" ../models.py >> model-noots/quality-models-noots.txt && grep -n "Quality" ../crud.py >> crud-noots/quality-crud-noots.txt && grep -n "Persona" ../models.py >> model-noots/persona-models-noots.txt && grep -n "Persona" ../crud.py >> crud-noots/persona-crud-noots.txt && grep -n "Trait" ../models.py >> model-noots/trait-models-noots.txt && grep -n "Trait" ../crud.py >> crud-noots/trait-crud-noots.txt

grep -n "Archetype" ../models.py >> model-noots/AM.txt && grep -n "Archetype" ../crud.py >> crud-noots/arch-crud-noots.txt && grep -n "Quality" ../models.py >> model-noots/quality-models-noots.txt && grep -n "Quality" ../crud.py >> crud-noots/quality-crud-noots.txt && grep -n "Persona" ../models.py >> model-noots/persona-models-noots.txt && grep -n "Persona" ../crud.py >> crud-noots/persona-crud-noots.txt && grep -n "Trait" ../models.py >> model-noots/trait-models-noots.txt && grep -n "Trait" ../crud.py >> crud-noots/trait-crud-noots.txt

then, in each of model-noots and crud-noots, you can do:
sort -n -u *.txt > noots.txt 

awk '{
    gsub(/\.txt$/, "", FILENAME)
    sub(/^.*\//, "", FILENAME)
    prefix = substr(FILENAME, 1, 1)
    line = prefix ":" $0
    if (seen[$0] == "") {
        seen[$0] = prefix
    } else {
        seen[$0] = seen[$0] "," prefix
    }
    lines[$0] = line
}
END {
    for (l in lines) {
        print "[" seen[l] "] " l
    }
}' red.txt blue.txt yellow.txt | sort -n > merged_deduplicated.txt
