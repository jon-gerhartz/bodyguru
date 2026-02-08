async function getOptions(url, land_id, required=false, showDefaultText=false, value_col='', force=false) {
		const resp = await fetch(url)
		const jsonData = await resp.json() 
		const data = await jsonData.data	
		const length = await data.length
		const land = document.getElementById(land_id)
		if (!land) {
			return
		}
		if (!force && land.dataset.optionsLoaded === 'true') {
			return
		}
		land.innerHTML = ''
		if (required){
			land.setAttribute('required', true)
		}
		if (showDefaultText){
			const defaultOption = document.createElement('option')
			defaultOptionId = 'default_option'
			defaultOption.setAttribute('id', defaultOptionId)
			const dataName = await jsonData.name
			defaultOptionText = 'select ' + dataName
			defaultOption.innerHTML = defaultOptionText
			defaultOption.setAttribute('disabled', true)
			defaultOption.setAttribute('selected', true)
			defaultOption.value = ""
			land.appendChild(defaultOption)
		}
		for (let i = 0; i< length; i++) {
			const option = document.createElement('option')
			optionid = 'option_' + i
			option.setAttribute('id', optionid)
			const optObj =  await data[i]
			const formattedOption = optObj.name.charAt(0).toUpperCase() + optObj.name.slice(1)
			option.innerHTML = formattedOption
			if(value_col=='id'){
				option.setAttribute('value', optObj.id)
			} else{
				option.setAttribute('value', optObj.name)
			}
			option.setAttribute('objId', optObj.id)
			land.appendChild(option)
		}
		land.dataset.optionsLoaded = 'true'
	}

async function loadItem(url) {
		const resp = await fetch(url)
		const jsonData = await resp.json() 
		const data = await jsonData.data
		const workoutData = await data[0].workout_data_json
		return await workoutData;
}

async function displayWorkout(workoutDataPromise, landId, input=false){
		const land = document.getElementById(landId)
		land.innerHTML = ''
		const workoutData = await workoutDataPromise
		console.log(workoutData)
		const workoutDataLength = Object.keys(workoutData).length
		for (let i = 1; i < workoutDataLength+1; i++) {
			const row = document.createElement('div')
			row.classList.add('row')
			land.appendChild(row)
			const col = document.createElement('div')
			col.classList.add('col')
			land.appendChild(col)
			const setHeader = document.createElement('h4')
			setHeader.innerHTML = 'Set ' + i
			land.appendChild(setHeader)
			let exerciseList = document.createElement('ol')
			const sets = workoutData[i]
			const setsLength = Object.keys(sets).length
			for (let ii = 0; ii < setsLength; ii++) {
				const exerciselistListItem = document.createElement('li')
				exerciselistListItem.innerHTML = sets[ii]
				exerciseList.appendChild(exerciselistListItem)
			land.appendChild(exerciseList)
			}
		}
		if (input) {
			const inputObj = document.createElement('input')
			inputObj.setAttribute('name', 'workout_data')
			inputObj.setAttribute('value', JSON.stringify(workoutData))
			inputObj.setAttribute('type', 'hidden')
			land.appendChild(inputObj)
		}
}

function createFilters(dataCols, colData, landId, search=true){
	const land = document.getElementById(landId)
	const filterDiv = document.createElement('div')
	filterDiv.classList.add("collapse")
	filterDiv.setAttribute('id', 'filterInnerDiv')
	const dataColsLength = dataCols.length
	if (search){
		let search = document.createElement('input')
		search.classList.add('form-control')
		search.classList.add('mr-sm-2')
		search.setAttribute('type','search')
		search.setAttribute('placeholder','search by name')
		search.setAttribute('onkeyup', "searchResults(this)")
		filterDiv.appendChild(search)
		let br = document.createElement('br')
		filterDiv.appendChild(br)
	}
	
	for (let i=0; i< dataColsLength; i++){
		let row = document.createElement('div')
		row.classList.add('row')
		let rowId = 'filterItem' + i
		row.setAttribute('id', 'rowId')
		let head = document.createElement('h6')
		let filterItem = dataCols[i]
		let formattedItem = (filterItem[0].toUpperCase() + filterItem.slice(1)).replaceAll('_',' ')
		head.innerHTML = formattedItem
		row.appendChild(head)
		let colItems = colData[filterItem]
		let colItemsLength = colItems.length
		let col = document.createElement('div')
		col.classList.add('col')
		for (let ii=0; ii<colItemsLength; ii++){
			let innerRow = document.createElement('div')
			innerRow.classList.add('form-check')
			let formCheck = document.createElement('input')
			formCheck.classList.add('form-check-input')
			let formCheckId = 'filterFormCheck' + filterItem + ii
			formCheck.setAttribute('id', formCheckId)
			formCheck.setAttribute('type', 'checkbox')
			formCheck.setAttribute('filterObj', filterItem)
			formCheck.setAttribute('onclick', "filterResults(this)")
			filterVal = colItems[ii]
			formCheck.setAttribute('val',filterVal)
			let formCheckLabel = document.createElement('label')
			formCheckLabel.classList.add('form-check-label')
			formCheckLabel.setAttribute('for', formCheckId)
			formCheckLabel.innerHTML = filterVal
			innerRow.appendChild(formCheck)
			innerRow.appendChild(formCheckLabel)
			col.appendChild(innerRow)
		}
		row.appendChild(col)
		let br = document.createElement('br')
		filterDiv.appendChild(row)
		filterDiv.appendChild(br)
	}
	land.appendChild(filterDiv)
};

function createDateFilter(dataCols, colData, landId, search=true){
	const land = document.getElementById(landId)
	const dataColsLength = dataCols.length
	if (search){
		let search = document.createElement('input')
		search.classList.add('form-control')
		search.classList.add('mr-sm-2')
		search.setAttribute('type','search')
		search.setAttribute('placeholder','search by name')
		search.setAttribute('onkeyup', "searchResults(this)")
		land.appendChild(search)
		let br = document.createElement('br')
		land.appendChild(br)
	}
	
	for (let i=0; i< dataColsLength; i++){
		let row = document.createElement('div')
		row.classList.add('row')
		let rowId = 'filterItem' + i
		row.setAttribute('id', 'rowId')
		let head = document.createElement('h6')
		let filterItem = dataCols[i]
		let formattedItem = (filterItem[0].toUpperCase() + filterItem.slice(1)).replaceAll('_',' ')
		head.innerHTML = formattedItem
		row.appendChild(head)
		let colItems = colData[filterItem]
		let colItemsLength = colItems.length
		let col = document.createElement('div')
		col.classList.add('col')
		let dateInput = document.createElement('input')
		dateInput.setAttribute('type', 'date')
		dateInput.setAttribute('filterObj', filterItem)
		dateInput.setAttribute('onchange', "filterDateResults(this)")
		col.appendChild(dateInput)
		row.appendChild(col)	
		let br = document.createElement('br')
		land.appendChild(row)
		land.appendChild(br)
	}
};


function filterResults(self){
	filterObjType = self.getAttribute('filterObj')
	setsNodeList = document.querySelectorAll('[tag^=obj]'.replace('obj',filterObjType))
	sets = Array.from(setsNodeList)
	val = self.getAttribute('val')
	for (i = 0; i < sets.length; i++){
		set = sets[i]
		if (set.innerHTML != val){
			parentId = set.getAttribute('parentId')
			ele = document.getElementById(parentId)
			if(self.checked){
				ele.style.display = 'none'
			} else{
				ele.style.display = 'block'
			}
		}
	}
};

function filterDateResults(self){
	filterObjType = self.getAttribute('filterObj')
	setsNodeList = document.querySelectorAll('[tag^=obj]'.replace('obj',filterObjType))
	sets = Array.from(setsNodeList)
	val = self.value
	for (i = 0; i < sets.length; i++){
		set = sets[i]
		parentId = set.getAttribute('parentId')
		ele = document.getElementById(parentId)
		setVal = set.innerHTML
		if (setVal.includes(val)){
			ele.style.display = 'table-row'
		} else{
			ele.style.display = 'none'
			}
		}
	};

function searchResults(self){
	var searchStr = self.value.toLowerCase();
	var setsNodeList = document.querySelectorAll('[searchtag^=resultData]');
	var sets = Array.from(setsNodeList);
	for (i = 0; i < sets.length; i++){
		var set = sets[i];
		var parentId = set.getAttribute('parentId');
		var ele = document.getElementById(parentId);
		var setVal = set.innerHTML.toLowerCase();
			if (setVal.includes(searchStr)){
				ele.style.display = 'block';
			} 
			else {
				ele.style.display = 'none';
				}
		}
	};
