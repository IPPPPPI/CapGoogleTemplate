from app import app
import mongoengine.errors
from flask import render_template, flash, redirect, url_for
from flask_login import current_user
from app.classes.data import Animal, Comment
from app.classes.forms import AnimalForm, CommentForm
from flask_login import login_required
import datetime as dt

# This is the route to list all animals
@app.route('/animal/list')
@app.route('/animals')
# This means the user must be logged in to see this page
@login_required
def animalList():
    # This retrieves all of the 'animals' that are stored in MongoDB and places them in a
    # mongoengine object as a list of dictionaries name 'animals'.
    animals = Animal.objects()
    # This renders (shows to the user) the animals.html template. it also sends the animals object 
    # to the template as a variable named animals.  The template uses a for loop to display
    # each animal.
    return render_template('animals.html',animals=animals)

# This route will get one specific animal and any comments associated with that animal.  
# The animalID is a variable that must be passsed as a parameter to the function and 
# can then be used in the query to retrieve that animal from the database. This route 
# is called when the user clicks a link on animallist.html template.
# The angle brackets (<>) indicate a variable. 
@app.route('/animal/<animalID>')
# This route will only run if the user is logged in.
@login_required
def animal(animalID):
    # retrieve the animal using the animalID
    thisAnimal = Animal.objects.get(id=animalID)
    # If there are no comments the 'comments' object will have the value 'None'. Comments are 
    # related to animals meaning that every comment contains a reference to a animal. In this case
    # there is a field on the comment collection called 'animal' that is a reference the Animal
    # document it is related to.  You can use the animalID to get the animal and then you can use
    # the animal object (thisAnimal in this case) to get all the comments.
    theseComments = Comment.objects(animal=thisAnimal)
    # Send the animal object and the comments object to the 'animal.html' template.
    return render_template('animal.html',animal=thisAnimal,comments=theseComments)

# This route will delete a specific animal.  You can only delete the animal if you are the author.
# <animalID> is a variable sent to this route by the user who clicked on the trash can in the 
# template 'animal.html'. 
# TODO add the ability for an administrator to delete animals. 
@app.route('/animal/delete/<animalID>')
# Only run this route if the user is logged in.
@login_required
def animalDelete(animalID):
    # retrieve the animal to be deleted using the animalID
    deleteAnimal = Animal.objects.get(id=animalID)
    # check to see if the user that is making this request is the author of the animal.
    # current_user is a variable provided by the 'flask_login' library.
    if current_user == deleteAnimal.author:
        # delete the animal using the delete() method from Mongoengine
        deleteAnimal.delete()
        # send a message to the user that the animal was deleted.
        flash('The Animal was deleted.')
    else:
        # if the user is not the author tell them they were denied.
        flash("You can't delete a animal you don't own.")
    # Retrieve all of the remaining animals so that they can be listed.
    animals = Animal.objects()  
    # Send the user to the list of remaining animals.
    return render_template('animal.html',animals=animals)

# This route actually does two things depending on the state of the if statement 
# 'if form.validate_on_submit()'. When the route is first called, the form has not 
# been submitted yet so the if statement is False and the route renders the form.
# If the user has filled out and succesfully submited the form then the if statement
# is True and this route creates the new animal based on what the user put in the form.
# Because this route includes a form that both gets and animals data it needs the 'methods'
# in the route decorator.
@app.route('/animal/new', methods=['GET', 'POST'])
# This means the user must be logged in to see this page
@login_required
# This is a function that is run when the user requests this route.
def animalNew():
    # This gets the form object from the form.py classes that can be displayed on the template.
    form = AnimalForm()

    # This is a conditional that evaluates to 'True' if the user submitted the form successfully.
    # validate_on_submit() is a method of the form object. 
    if form.validate_on_submit():

        # This stores all the values that the user entered into the new animal form. 
        # Animal() is a mongoengine method for creating a new animal. 'newAnimal' is the variable 
        # that stores the object that is the result of the Animal() method.  
        newAnimal = Animal(
            # the left side is the name of the field from the data table
            # the right side is the data the user entered which is held in the form object.
            subject = form.subject.data,
            content = form.content.data,
            tag = form.tag.data,
            approval = form.approval.data,
            author = current_user.id,
            # This sets the modifydate to the current datetime.
            modify_date = dt.datetime.utcnow
        )
        # This is a method that saves the data to the mongoDB database.
        newAnimal.save()

        # Once the new animal is saved, this sends the user to that animal using redirect.
        # and url_for. Redirect is used to redirect a user to different route so that 
        # routes code can be run. In this case the user just created a animal so we want 
        # to send them to that animal. url_for takes as its argument the function name
        # for that route (the part after the def key word). You also need to send any
        # other values that are needed by the route you are redirecting to.
        return redirect(url_for('animal',animalID=newAnimal.id))

    # if form.validate_on_submit() is false then the user either has not yet filled out
    # the form or the form had an error and the user is sent to a blank form. Form errors are 
    # stored in the form object and are displayed on the form. take a look at animalform.html to 
    # see how that works.
    return render_template('animalform.html',form=form)


# This route enables a user to edit a animal.  This functions very similar to creating a new 
# animal except you don't give the user a blank form.  You have to present the user with a form
# that includes all the values of the original animal. Read and understand the new animal route 
# before this one. 
@app.route('/animal/edit/<animalID>', methods=['GET', 'POST'])
@login_required
def animalEdit(animalID):
    editAnimal = Animal.objects.get(id=animalID)
    # if the user that requested to edit this animal is not the author then deny them and
    # send them back to the animal. If True, this will exit the route completely and none
    # of the rest of the route will be run.
    if current_user != editAnimal.author:
        flash("You can't edit a animal you don't own.")
        return redirect(url_for('animal',animalID=animalID))
    # get the form object
    form = AnimalForm()
    # If the user has submitted the form then update the animal.
    if form.validate_on_submit():
        # update() is mongoengine method for updating an existing document with new data.
        editAnimal.update(
            subject = form.subject.data,
            content = form.content.data,
            tag = form.tag.data,
            modify_date = dt.datetime.utcnow
        )
        # After updating the document, send the user to the updated animal using a redirect.
        return redirect(url_for('animal',animalID=animalID))

    # if the form has NOT been submitted then take the data from the editAnimal object
    # and place it in the form object so it will be displayed to the user on the template.
    form.subject.data = editAnimal.subject
    form.content.data = editAnimal.content
    form.tag.data = editAnimal.tag


    # Send the user to the animal form that is now filled out with the current information
    # from the form.
    return render_template('animalform.html',form=form)

#####
# the routes below are the CRUD for the comments that are related to the animals. This
# process is exactly the same as for animals with one addition. Each comment is related to
# a specific animal via a field on the comment called 'animal'. The 'animal' field contains a 
# reference to the Animal document. See the @app.route('/animal/<animalID>') above for more details
# about how comments are related to animals.  Additionally, take a look at data.py to see how the
# relationship is defined in the Animal and the Comment collections.

@app.route('/comment/new/<animalID>', methods=['GET', 'POST'])
@login_required
def commentNew(animalID):
    animal = Animal.objects.get(id=animalID)
    form = CommentForm()
    if form.validate_on_submit():
        newComment = Comment(
            author = current_user.id,
            animal = animalID,
            content = form.content.data
        )
        newComment.save()
        return redirect(url_for('animal',animalID=animalID))
    return render_template('commentform.html',form=form,animal=animal)

@app.route('/comment/edit/<commentID>', methods=['GET', 'POST'])
@login_required
def commentEdit(commentID):
    editComment = Comment.objects.get(id=commentID)
    if current_user != editComment.author:
        flash("You can't edit a comment you didn't write.")
        return redirect(url_for('animal',animalID=editComment.animal.id))
    animal = Animal.objects.get(id=editComment.animal.id)
    form = CommentForm()
    if form.validate_on_submit():
        editComment.update(
            content = form.content.data,
            modifydate = dt.datetime.utcnow
        )
        return redirect(url_for('animal',animalID=editComment.animal.id))

    form.content.data = editComment.content

    return render_template('commentform.html',form=form,animal=animal)   

@app.route('/comment/delete/<commentID>')
@login_required
def commentDelete(commentID): 
    deleteComment = Comment.objects.get(id=commentID)
    deleteComment.delete()
    flash('The comments was deleted.')
    return redirect(url_for('animal',animalID=deleteComment.animal.id)) 
