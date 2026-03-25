alter table public.workout_history
add column if not exists exercise_total integer not null default 0;

alter table public.workout_history
add column if not exists exercise_done integer not null default 0;
