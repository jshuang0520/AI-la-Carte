# Summary

Checked changes to provide information to NULL data using GIS data, discussed what is required on priority, strengths and weaknesses of person.

## Adding GIS data
### transform.py problems
1. Only the first non-null value from `start1_{weekday}`, `start1_{weekday}`, `start1_{weekday}` are taken and therefore much data is gone.
2. Merging is done without proper consideration of `Frequency`, `Starting Time` and other important variables.
3. `Frequency` does not take `1st, 2nd and 3rd of the Month` and other similar values, and `Every Other Week`

### analyze_layer_transform.py TODO
1. `Starting Time` and `Ending Time` contains `As Needed` but the code treats as error and it coerces.
2. For a single row, if `Hours` has 3 subrows and `ByAppointmentOnly` contains only 1 value, then for each subrow, the same `ByAppointmentOnly` value should be considered.
3. Merge GIS data with CAFB data

## Priority tasks
1. Runnable code (Peeyush)
2. Translation (Need to discuss when translation should be used along with Krishna)
3. Additional data from GIS can be taken later

## Weaknesses
### Peeyush
1. Explaining can be a bit better. Focus on the gist first and then go to details
2. If you write complex code, better to divide dividable parts into a function so that it is easy for other people to read.
3. Do not stick to Pandas. If there are other ways people are comfortable with, they might feel a little uncomfortable.

### Johnson
1. Do not over complicate the given task.
