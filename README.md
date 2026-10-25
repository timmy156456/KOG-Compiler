*This repo is a learning project for me. I am not accepting outside contributions or pull requests.*



# Variables and Types
```
var = value
```
OR
```
value = var
```

Forwards and backwards assignment. If you want to assign x to y as y = x (backwards assigned) then you need to write it as "(x) = y".

Variable types are determined at compile-time by the value that it is assigned.
Ints
```
x = 5

10 = x
```
These are int variables

Bools
```
x = true

x = False

x = TRUE
```
These are all examples of ways to write a boolean, caps doesn't matter.

Comments
```
~This is a full line comment

~This is a block comment, a newline character is appended to the end of this so it can also serve as an optional line terminator~
```
Example:
```
x = 5 ~~ y = x
```
Booleans (bools) are treated as numbers, 1 for true, -1 for false.
```
x = 5 * false ~x's value is -5 because 5 * -1 is -5
```
## String Type

Strings are created by using double or single quotes ("Hello, World!" or 'Hello, World!'). They also have escape sequences like \n, and you can embed single quotes in a double quoted string, and double quotes in a single quoted string.

String creation and concatenation example:
```
myString1 = "Hello, "

myString2 = "World!"

finalString = strcon(myString1, myString2)

println(finalString)   ~will print "Hello, World!"
```
Strings can also be formatted, almost exactly like python:
```
x = 5

str = f"number is {x}" ~formats to "number is 5"

~multi line string:
y = "line 1
line 2
line 3"
```

Strings can be sliced very similarly to python as str[start:stop\:step]

Taking string input and indexing/slicing example:
```
str = "Hello, World!"

hello = str[:5]   ~will return "Hello" because the empty start means 0, and goes to index 5 exclusive which is "o"

h = str[0]        ~will return "H" because index 0 of str is "H"

~you can reverse strings too

str = str[::-1]   ~this will reverse the string, this one will become "!dlroW ,olleH"


~taking input is very easy, its input(charLen), charLen is the max number of bytes/characters to take from user input

inp = input(32)   ~takes 32 bytes/characters of input
```
If there's an error while slicing or indexing a string it will print "Err: BadSlice" and terminate the program.

Strings can be compared with the equal() method, it takes two object inputs, returns true if their direct contents are equal, very useful for comparing strings.


## Arrays

Arrays are created with `Array[size]` to create a fixed size, or `Array->[item1, item2, otherItems]` to fill the array upon creation.

You can slice arrays just as you can with strings, but as a shallow copy, not a deep copy.

Arrays also hold multiple datatypes, you can get the datatype at an index of an array with the itype(array, index) function. 0 means native type (int, bool), 1 means object, 2 means array.

You can print an array out with the printarr(array) or printarrln(array) function.


Examples:
```
arr = Array[10] ~creates an array with 10 elements

filledArr = Array->[1, 2, "hi", 3] ~arrays hold multiple types

y = filledArr[0] as int   ~specifying type being taken out

filledArr[1] = y   ~dont have to specify type when setting an element of an array
```
The type being taken out of an array must be specified along with the index.


# Operators
Unary operators:

"-" this negates a value

"+" this makes a value its absolute value

Regular operators:
```
x + y ~addition

x - y ~subtraction

x * y ~multiplication

x ^ y ~exponentiation

x // y ~int division, must be used by int variable types and currently only supports positive numbers

x % y ~modulos
```
Boolean operators:

`==` checks if two values are equal

`!=` OR `!` checks if two values are not equal, both mean the same thing

`<` checks if left is less than right value

`>` checks if left is more than right value

`<=` or `=<` checks if left is less than or equal to right value

`>=` or `=>` checks if left is more than or equal to right value


# If Statements
```
if condition
   body
end
```
and
```
if condition
   body
else
   elseBody
end
```
and
```
if condition
   body
else if condition
   elseIfBody
end
```
and
```
if condition
   body
else if condition
   elseIfBody
else
   elseBody
end
```

You can also directly use variables as the condition:
```
x = 1
if x ~it compares x's value to a true boolean value, which is 1 so this is true
   print(x)
end
```
```
x = 0
if x ~this one will be false since it is not equal to 1
   print(x)
end
```


# While Loops
```
while condition
   body
end
```
There are also `continue` and `break` statements, just like any other language.


Example:
```
i = 0
while i < 5
   print(i)
   i = i + 1
end
```

# For Loops
```
for variable in range(start, stop, step) ~or (start stop), or (stop) or just () as default 10
   body
end
```
For loops also have `continue` and `break` statements.

Example:
```
for i in range()
   print(i)      ~will print all numbers from 0-9 because default is 10
end
```
For loops can loop through arrays too.
```
for variable in array as type
   body
end
```
Example:
```
arr = Array->[1, 3, 5, 7, 9]
for num in arr as int
   print(num)
end
~this will print "13579" and works with any type

~you can also parse strings:
str = "Hello, World!"
for char in str
   print(char, "")   ~"H e l l o ,   W o r l d ! "
end
```
Using a for loop to parse through a string only creates one object for the entire loop, if you want to use that character somewhere else without it being overwritten you need to create a copy of it which can be easily done with string slicing (str\[:]) which automatically copies the entire string into a new object.


# Creating and Using Functions
```
def returnType functionName(parameterType parameterName)

   body
    
   return ~every function MUST end with a return statement, but they dont all have to return something
```
Examples:
```
def int sum(int x, int y) ~creates a function with an int return type and two int parameters

   summed = x + y
    
   return summed
```
```
x = 5

def none increment() ~creates a function with no return type and no parameters

   x = x + 1
    
   return ~dont have to return a value here
```
Functions can only return one item at a time.

Functions can be called by putting parenthesis after the functions name, and values inside of those parenthesis.
```
z = sum(1, 2)
```

# Premade Functions
```
print(param, param, param) ~takes infinite arguments, no newline character printed after regular arguments

println(param, param, param) ~takes infinite arguments, newline character printed after regular arguments

printarr(array) ~takes only one Array param, prints the formatted array

printarrln(array) ~takes only one Array param, same thing as printarr() but adds a newline character after argument

itype(array, index) ~takes an array and array index, returns the type of the item at that index (0 for native, 1 for object, 2 for array)

strint(value) ~turns a string into an integer, errors with code 127 if impossible

intput(bufferSize) ~takes an integer input of size bufferSize, bufferSize 28 is the min that can hold the largest int, but nothing is stopping you from allocating more space for empty zeros

len(string) ~returns the length of a string, does NOT calculate length, just returns the string objects length
~every string has a built in length property, so it does not have to calculate the length and can just return the property

input(charLen) ~takes charLen bytes/characters of input from terminal

string[start:stop:step] ~splits a string starting at start, ending at step, and stepping by step

string[index] ~creates a new string object of size 1 containing the character at that index of the string

strcon(str1, str2) ~returns a new string that is the result of concatenating str1 with str2

refcount(obj) ~returns the number of variables that directly hold a pointer to obj

equal(obj1, obj2) ~compares two objects to each other, returns true if direct contents are equal

exit(code?) ~exits the program with given code value, if code value is not provided it will default to 0
```


# Notes
This is my first compiler.

I worked on this solo.

No AI was used to write any code at all, including the assembly.

All assembly written in the file is my own work.

I do not have floats, or classes in the language yet.

# How to Use

It can read from any regular text file, but I use .kog as the file suffix.

Run it in terminal with "{python or python3} {path to compiler} {input file} {output file}" and a "--no-optim" option for removing optimizations.

After you have your paths in, just run the command and it will write into a .s (assembly) file.

You can run the assembly file by running "./file.s" in your terminal, or by using a plugin with VSCode.
