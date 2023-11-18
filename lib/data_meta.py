exercise_filter_cols = ['type', 'equipment', 'muscle_group_name']
workout_filter_cols = ['type']
log_filter_cols = ['created_at']

def create_filer_col_dict(filter_cols, data):
	resp = {}
	for col in filter_cols:
		unique_col_vals = data[col].unique().tolist()
		resp[col] = unique_col_vals
	return resp