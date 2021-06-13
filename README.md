# FileSorter
A file sorter built in PyQt. I started working on this around 10/2020 right after getting hired at CAHFS San Bernardino 
where their file organization was in bad shape; I thought this would help but scrapped that thought after realizing that running 
scripts on company networks seemed like a bad idea. While functional, I would only really use this if there was no prior 
folders/organization as I didn't implement a way to revert changes. :P

<p align="center">
    <img width=400 src="https://raw.githubusercontent.com/koisland/FileSorter/main/docs/ui.png?token=AO7RZYIGFYIW2PFDHTEHS33AYWQ5S">
</p>

## Sorting
Sorts based on three categories: **date**, **file type**, and **keywords**.

Categories can be omitted or reordered and will result in different nested arrangement of files.

<p align="center">
   <img width=300 src="https://raw.githubusercontent.com/koisland/FileSorter/main/docs/date_keyword.png?token=AO7RZYJ4ZRSDD5D65LZQFMTAYWTA6"/>
   <img width=300 src="https://raw.githubusercontent.com/koisland/FileSorter/main/docs/keyword_date.png?token=AO7RZYIQVIBD3QQEJBU6RI3AYWTLE"/>
</p>
<p align="center">
   <img width=300 src="https://raw.githubusercontent.com/koisland/FileSorter/main/docs/date_keyword_tree.png?token=AO7RZYI3EZOLHG62I47UPELAYWTN6"/>
   <img width=300 src="https://raw.githubusercontent.com/koisland/FileSorter/main/docs/keyword_date_tree.png?token=AO7RZYPBCUVECEQDUG6TWCDAYWTOE"/>
</p>
<p align="center">
   <b>Sort by <em>date then keyword</em> (left) and by <em>keyword then date</em> (right)</b>
</p>

1. Date
   * Sorts based on the day, month or year a file was created, accessed, or modified.
   * Date can be optionally provided to only sort files that fall within a timeframe.
2. File Type
   * Sorts based on file types defined by mimetypes.
   * File extensions can be optionally added and used as sort parameters.
3. Keyword
   * Sorts based on provided keywords which can be grouped in folders.
   
## TO-DO
* Finish statistics and graphs page.
* Add an option to reverse a sort.

