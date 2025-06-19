def hello( ):
    print( "Hello, World!" )


def   add_numbers(a,b):
  return a+b

class MyClass:
  def __init__(self,name):
    self.name=name
  
  def get_name( self ):
    return self.name


if __name__=="__main__":
  obj=MyClass("test")
  result=add_numbers(1,2)
  hello()