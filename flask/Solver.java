import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.OWLEntity;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLLogicalAxiom;
import org.semanticweb.owlapi.model.OWLSubClassOfAxiom;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyManagerFactory;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLAxiom;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLOntologyID;
import org.semanticweb.owlapi.util.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.Node;
import org.semanticweb.owlapi.reasoner.NodeSet;
import org.semanticweb.owlapi.reasoner.ConsoleProgressMonitor;
import org.semanticweb.owlapi.reasoner.IndividualNodeSetPolicy;
import org.semanticweb.owlapi.reasoner.structural.StructuralReasonerFactory;

import org.semanticweb.HermiT.Configuration;
import org.semanticweb.HermiT.ReasonerFactory;

import java.io.File;
import java.util.stream.*;
import java.util.List;
import java.util.Set;
import java.util.ArrayList;

public class Solver {
    public static OWLReasoner reasoner;
    public static OWLOntologyManager m;
    
	public static void main(String[] args) {
        // Check arguments
        if (args.length < 2 ){
            System.out.print("Error! pass two .owl file paths.");
            return;
        }
        
        // create OntologyManager
		m = OWLManager.createOWLOntologyManager();
        
        // Load main ontology file
        File inputOntologyFile = new File(args[0]);
		OWLOntology ontology;
        try {
			ontology = m.loadOntologyFromOntologyDocument(inputOntologyFile);
		}catch(OWLOntologyCreationException e) {
			System.out.print("Error! Failed to load ontology.");
            return;
		}
        //showOnto(ontology);
        //System.out.print("-----------------------------");
        
        ReasonerFactory factory = new ReasonerFactory();
        reasoner = factory.createReasoner(ontology);
        if (!isConsistent()){
            System.out.print("Error! The ontology is not consistent.");
            return;
        }
        
        OWLOntology inferred;
        try {
			inferred = infer(ontology);
		}catch(OWLOntologyCreationException e) {
			System.out.print("Error! Failed to infer ontology.");
            return;
		}
        
        // Load question ontology
        OWLOntologyManager m2 = OWLManager.createOWLOntologyManager();
		File questionOntologyFile = new File(args[1]);
		OWLOntology question;
        try {
			question = m2.loadOntologyFromOntologyDocument(questionOntologyFile);
		}catch(OWLOntologyCreationException e) {
			System.out.print("Error! Failed to load question.");
            return;
		}
        
        //find answer
        getAnswer(question);
	}
    
    private static void showOnto(OWLOntology o){
        o.axioms().forEach(System.out::print);
    }
    
    private static OWLOntology infer(OWLOntology o) throws OWLOntologyCreationException {
        List<InferredAxiomGenerator<? extends OWLAxiom>> generators=new ArrayList<InferredAxiomGenerator<? extends OWLAxiom>>();
        
        /*
         * Every N is a N.
         */
        generators.add(new InferredSubClassAxiomGenerator());
        
        /*
         * I is a N.
         */
        generators.add(new InferredClassAssertionAxiomGenerator());
        
        /*
         * If X OP. Y then X OP./topObjectProperty
         */
        generators.add(new InferredSubObjectPropertyAxiomGenerator());
        
        /*
         * 
         */
        generators.add(new InferredDataPropertyCharacteristicAxiomGenerator());
        
        /*
         * No N is a N.
         */
        generators.add(new InferredDisjointClassesAxiomGenerator());
        
        /*
         * 
         */
        generators.add(new InferredEquivalentClassAxiomGenerator());
        
        /*
         * 
         */
        generators.add(new InferredEquivalentDataPropertiesAxiomGenerator());
        
        /*
         * 
         */
        generators.add(new InferredObjectPropertyCharacteristicAxiomGenerator());
        
        /*
         * I1 OP I2.
         */
        generators.add(new InferredPropertyAssertionGenerator());
        
        /*
         * 
         */
        generators.add(new InferredSubDataPropertyAxiomGenerator());
        
        /*
         * 
         */
        generators.add(new InferredSubObjectPropertyAxiomGenerator());
        
        InferredOntologyGenerator iog = new InferredOntologyGenerator(reasoner,generators);
        OWLOntology inferredAxiomsOntology = m.createOntology();   
        //iog.fillOntology(m, inferredAxiomsOntology);
        iog.fillOntology(m.getOWLDataFactory(), inferredAxiomsOntology);
        return inferredAxiomsOntology;
    }
    
    private static boolean isConsistent(){
        return reasoner.isConsistent();
    }
    
    private static void getAnswer(OWLOntology question){
        // Convert the question axiom to class expression format
        List<OWLLogicalAxiom> queries = question.logicalAxioms().collect(Collectors.toList());
        OWLClassExpression query = ((OWLSubClassOfAxiom)queries.get(0)).getSubClass();
        //System.out.print(query);
        //System.out.print("-----------------------------");
        
        if(reasoner.isSatisfiable(query)){
            // Get satisfied individual
            NodeSet<OWLNamedIndividual> indNodeSet = reasoner.getInstances(query, true);
            Set<Node<OWLNamedIndividual>> indNodes = indNodeSet.getNodes();
            //System.out.print(indNodes.size());
            String split = "";
            for(OWLNamedIndividual ind : indNodeSet.getFlattened()){
                System.out.print(split + ind);
                split = "*";
            }
            
            // Get subclasses
            NodeSet<OWLClass> subNodeSet = reasoner.getSubClasses(query, false);
            Set<Node<OWLClass>> subNodes = subNodeSet.getNodes();
            System.out.print("$");
            split = "";
            for(OWLClass sub : subNodeSet.getFlattened()){
                if ("owl:Nothing".equals(sub.toString())) continue;
                System.out.print(split + sub);
                split = "*";
            }
            
            // Get super classes
            NodeSet<OWLClass> superNodeSet = reasoner.getSuperClasses(query, false);
            Set<Node<OWLClass>> superNodes = superNodeSet.getNodes();
            System.out.print("$");
            split = "";
            for(OWLClass sup : superNodeSet.getFlattened()){
                if ("owl:Thing".equals(sup.toString())) continue;
                System.out.print(split + sup);
                split = "*";
            }
        }
    }
}
